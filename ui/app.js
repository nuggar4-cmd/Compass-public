'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const desktop = new URLSearchParams(window.location.search).get('desktop') === '1';
  const all = 'All apps';
  const catalogFields = ['id', 'name', 'category', 'description', 'host', 'url', 'glyph'];
  const startupLimitMs = 8000;
  const favoritesLimitMs = 5000;
  const languageKey = 'compass-language';
  const turkishCategories = new Map([
    [all, 'Tümü'], ['Browsers', 'Tarayıcılar'], ['Development', 'Geliştirme'], ['Creative', 'Tasarım'],
    ['Utilities', 'Araçlar'], ['Media', 'Medya'], ['Productivity', 'Üretkenlik'], ['Gaming', 'Oyun'],
    ['Communication', 'İletişim'], ['Education', 'Eğitim'],
  ]);
  const turkishTags = new Map([
    ['archive', 'arşiv'], ['audio', 'ses'], ['clipboard', 'pano'], ['editor', 'düzenleme'],
    ['image', 'görsel'], ['messaging', 'mesajlaşma'], ['music', 'müzik'], ['notes', 'not alma'],
    ['password', 'şifre parola'], ['recording', 'kayıt'], ['screen reader', 'ekran okuyucu'],
    ['sound', 'ses'], ['spreadsheet', 'hesap tablosu'], ['streaming', 'yayın'], ['video editor', 'video düzenleme'],
  ]);
  const turkishBridgeMessages = new Map([
    ['Opening cancelled.', 'Açma işlemi iptal edildi.'],
    ['A link request is already open.', 'Bir bağlantı açma isteği zaten bekliyor.'],
    ['Could not open your browser. Please try again.', 'Tarayıcı açılamadı. Lütfen tekrar dene.'],
    ['Could not open the website. Please try again.', 'Site açılamadı. Lütfen tekrar dene.'],
    ['Compass blocked this address because it did not pass the catalog check.', 'Bu adres katalog denetiminden geçmediği için engellendi.'],
  ]);
  const checkReasons = new Map([
    ['publisher-listed', ['verified', 'The full address matches a reviewed publisher page in the Compass catalog.', 'Adresin tamamı Compass kataloğunda incelenmiş bir yayıncı sayfasıyla eşleşiyor.']],
    ['unlisted', ['unverified', 'Compass has no verified match for this address. Find the publisher’s official page before opening it.', 'Compass bu adres için doğrulanmış bir eşleşme bulamadı. Açmadan önce yayıncının resmî sayfasını bul.']],
    ['empty', ['blocked', 'Paste the full HTTPS address to check it.', 'Denetlemek için tam HTTPS adresini yapıştır.']],
    ['malformed', ['blocked', 'The address format is invalid. Avoid opening it.', 'Adresin biçimi geçersiz. Bu bağlantıyı açma.']],
    ['scheme', ['blocked', 'Compass checks addresses that start with HTTPS. Avoid opening this link.', 'Compass HTTPS ile başlayan adresleri denetler. Bu bağlantıyı açma.']],
    ['credentials', ['blocked', 'The address contains a username or password. Avoid opening it.', 'Adres kullanıcı adı veya parola içeriyor. Bu bağlantıyı açma.']],
    ['nonpublic', ['blocked', 'The address needs a public domain name. Avoid opening it.', 'Denetim için herkese açık bir alan adı gerekiyor. Bu bağlantıyı açma.']],
    ['port', ['blocked', 'The address specifies a connection port that Compass does not review. Avoid opening it.', 'Adres, Compass’ın denetim kapsamı dışında bir bağlantı noktası belirtiyor. Bu bağlantıyı açma.']],
    ['encoded-authority', ['blocked', 'The server name contains characters Compass cannot verify. Avoid opening this link.', 'Adresin sunucu adında denetlenemeyen karakterler var. Bu bağlantıyı açma.']],
    ['local-address', ['blocked', 'The address uses a private or local IP address. Avoid opening it.', 'Adres özel veya yerel bir IP adresi kullanıyor. Bu bağlantıyı açma.']],
  ]);
  const checkLabels = {
    verified: ['verified', 'Safe', 'Güvenli'],
    unverified: ['caution', 'Unverified', 'Doğrulanamadı'],
    blocked: ['blocked', 'Blocked', 'Engellendi'],
  };
  const localizedText = Array.from(document.querySelectorAll('[data-tr]'), el => [el, el.textContent]);
  const localizedAttributes = [['data-tr-label', 'aria-label'], ['data-tr-placeholder', 'placeholder']]
    .flatMap(([translation, attribute]) => Array.from(document.querySelectorAll(`[${translation}]`),
      el => [el, attribute, el.getAttribute(attribute), el.getAttribute(translation)]));
  const state = { apps: [], category: all, query: '', sort: 'featured', view: 'discover', selected: null, busy: false };
  const blocked = new Map();
  const favorites = new Set();
  const pendingFavorites = new Set();
  let favoritesStatus = desktop ? 'loading' : 'ready';
  let desktopApi;
  let catalogAttempt;
  let catalogError;
  let toastTimer;
  let linkCheck = {};

  const copy = (english, turkish) => document.documentElement.lang === 'tr' ? turkish : english;
  const categoryLabel = category => copy(category, turkishCategories.get(category) || category);
  const bridgeMessage = message => copy(message, turkishBridgeMessages.get(message) || message);

  function preferredLanguage() {
    try {
      const saved = localStorage.getItem(languageKey);
      if (saved === 'tr' || saved === 'en') return saved;
    } catch (_) {
      // A local renderer may limit storage. The interface still works without a saved preference.
    }
    return /^tr(?:-|$)/i.test(navigator.language) ? 'tr' : 'en';
  }

  function applyLayout(layout) {
    $('cards').classList.toggle('list-layout', layout === 'list');
    $('layout-picker').querySelectorAll('button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.layout === layout));
    });
  }

  function updatePageTitle() {
    $('page-title').textContent = document.querySelector(`.nav[data-view="${state.view}"] [data-tr]`).textContent;
  }

  function applyLanguage(language) {
    document.documentElement.lang = language;
    $('language').value = language;
    localizedText.forEach(([el, english]) => { el.textContent = copy(english, el.dataset.tr); });
    localizedAttributes.forEach(([el, attribute, english, turkish]) => el.setAttribute(attribute, copy(english, turkish)));
    document.querySelectorAll('.filter').forEach(button => { button.textContent = categoryLabel(button.dataset.category); });
    updatePageTitle();
    updateStartupCopy();
    renderLinkCheck();
    if (state.apps.length) render();
  }

  const text = (tag, value, className) => {
    const el = document.createElement(tag);
    el.textContent = value;
    if (className) el.className = className;
    return el;
  };

  function notify(message) {
    $('toast').textContent = message;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $('toast').textContent = ''; }, 5000);
  }

  function normalizeSearch(value) {
    return value.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replaceAll('ı', 'i');
  }

  function setCatalogView(view) {
    $('discover-page').classList.toggle('startup-layout', desktop && view !== 'ready');
    $('catalog-loading').hidden = view !== 'loading';
    $('load-error').hidden = view !== 'error';
    $('catalog-results').hidden = view !== 'ready';
  }

  function updateStartupCopy() {
    $('catalog-loading-title').textContent = catalogAttempt?.requested
      ? copy('Loading the app catalog…', 'Uygulama kataloğu yükleniyor…')
      : copy('Connecting to Compass…', 'Compass’a bağlanılıyor…');
    $('catalog-loading-detail').textContent = catalogAttempt?.requested
      ? copy('Reading the publisher addresses stored with Compass.', 'Kayıtlı yayıncı adresleri okunuyor.')
      : copy('Waiting for the desktop window to respond.', 'Masaüstü uygulamasının yanıtı bekleniyor.');
    if (catalogError) $('load-error-message').textContent = copy(...catalogError);
  }

  function setView(view) {
    const favoritesViewChanged = (state.view === 'favorites') !== (view === 'favorites');
    if (state.view === 'checker' && view !== 'checker') {
      $('link-address').value = '';
      linkCheck = {};
      renderLinkCheck();
    }
    state.view = view;
    document.querySelectorAll('.nav').forEach(button => {
      const active = button.dataset.view === view;
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    $('privacy-page').hidden = view !== 'privacy';
    $('checker-page').hidden = view !== 'checker';
    $('discover-page').hidden = view === 'privacy' || view === 'checker';
    updatePageTitle();
    $('discover-title').hidden = view !== 'discover';
    $('library-title').hidden = view !== 'library';
    $('favorites-title').hidden = view !== 'favorites';
    window.scrollTo(0, 0);
    if (view === 'checker') renderLinkCheck();
    if (favoritesViewChanged && state.apps.length) render();
    $('page-title').focus({ preventScroll: true });
  }

  function checkerBridge() {
    const api = desktop ? window.pywebview?.api : null;
    return typeof api?.inspect_link === 'function' ? api : null;
  }

  function renderLinkCheck() {
    const api = checkerBridge();
    const { checking, error, result, explanation } = linkCheck;
    $('link-address').disabled = !api;
    $('inspect-link').disabled = !api;
    $('inspect-link').setAttribute('aria-disabled', String(checking === true));
    const status = $('checker-availability');
    if (!api) {
      status.textContent = desktop
        ? copy('The desktop connection for link checks is unavailable.', 'Bağlantı denetimi için masaüstü bağlantısına erişilemiyor.')
        : copy('Use the Compass desktop app to check a link.', 'Bağlantı denetimi için Compass masaüstü uygulamasını aç.');
    } else if (checking) {
      status.textContent = copy('Checking the address…', 'Adres denetleniyor…');
    } else {
      status.textContent = error ? copy('Compass could not check this address. Try again.', 'Compass bu adresi denetleyemedi. Tekrar dene.') : '';
    }

    const verdict = $('link-check-result');
    const badge = $('link-check-badge');
    const publisher = $('link-check-publisher');
    const reason = $('link-check-reason');
    verdict.hidden = !result;
    if (result) {
      const [tone, english, turkish] = checkLabels[result.status];
      badge.className = `security-label security-label--${tone}`;
      badge.textContent = copy(english, turkish);
      publisher.textContent = result.publisher;
      publisher.hidden = !result.publisher;
      reason.textContent = copy(...checkReasons.get(result.reason).slice(1));
    } else {
      badge.textContent = '';
      publisher.textContent = '';
      reason.textContent = '';
    }

    const explain = $('explain-link');
    const working = explanation?.status === 'working';
    explain.disabled = typeof api?.explain_link !== 'function';
    explain.setAttribute('aria-disabled', String(working));
    const explanationLine = $('ai-explanation');
    if (working) {
      explanationLine.textContent = copy('Asking the local AI…', 'Yerel AI açıklama hazırlıyor…');
    } else if (explanation?.language === document.documentElement.lang) {
      explanationLine.textContent = explanation.text || copy(
        'Local AI is unavailable. Start Ollama with the qwen2.5:0.5b model installed, then try again.',
        'Yerel AI kullanılamıyor. Ollama’yı başlat ve qwen2.5:0.5b modeli yüklüyken tekrar dene.');
    } else {
      explanationLine.textContent = '';
    }
    explanationLine.hidden = !explanationLine.textContent;
  }

  async function inspectLink(event) {
    event.preventDefault();
    const api = checkerBridge();
    if (!api || linkCheck.checking) return;
    const request = linkCheck = { checking: true };
    renderLinkCheck();
    try {
      const response = await api.inspect_link($('link-address').value);
      const [status] = checkReasons.get(response?.reason) || [];
      if (!status || status !== response.status) throw new Error('Invalid inspection result');
      const publisher = status === 'verified' && typeof response.publisher === 'string' ? response.publisher : '';
      request.result = { status, reason: response.reason, publisher };
    } catch (_) {
      request.error = true;
    } finally {
      request.checking = false;
      if (linkCheck === request) renderLinkCheck();
    }
  }

  async function explainLink() {
    const api = checkerBridge();
    const request = linkCheck;
    if (typeof api?.explain_link !== 'function' || !request.result || request.explanation?.status === 'working') return;
    const language = document.documentElement.lang;
    request.explanation = { status: 'working', language };
    renderLinkCheck();
    let explanation = '';
    try {
      const response = await api.explain_link(request.result.reason, language);
      if (response?.status === 'ready' && typeof response.explanation === 'string' && response.explanation.length <= 700) {
        explanation = response.explanation.trim();
      }
    } catch (_) {
      // The inspection still works when optional AI is unavailable.
    }
    request.explanation = { status: 'finished', language, text: explanation };
    if (request === linkCheck) renderLinkCheck();
  }

  function reset() {
    state.category = all;
    state.query = '';
    state.sort = 'featured';
    $('search').value = '';
    $('sort').value = 'featured';
    render();
  }

  function updatePublisherLabel(label, isBlocked) {
    label.textContent = isBlocked ? copy('Blocked', 'Engellendi') : copy('Safe', 'Güvenli');
    label.className = isBlocked ? 'security-label security-label--blocked' : 'security-label security-label--verified';
  }

  function hasNotice(app) {
    return typeof app.notice === 'string' && app.notice.trim() !== '';
  }

  function showBlocked(message) {
    const cardLabel = Array.from($('cards').children)
      .find(card => card.dataset.appId === state.selected.id)?.querySelector('.security-label');
    if (cardLabel) updatePublisherLabel(cardLabel, true);
    $('detail-verification').hidden = true;
    $('verification-scope').hidden = true;
    $('dialog-note').textContent = copy('Choose another listing to visit a website.', 'Bir siteyi açmak için başka bir uygulama seç.');
    const openButton = $('open-official');
    const hadFocus = document.activeElement === openButton;
    openButton.disabled = true;
    const label = text('strong', copy('Blocked', 'Engellendi'), 'security-label security-label--blocked');
    const reason = message ? bridgeMessage(message) : copy('The destination did not pass Compass’s catalog checks.', 'Adres Compass’ın katalog denetiminden geçmedi.');
    $('dialog-status').textContent = '';
    $('blocked-destination').replaceChildren(label, ' ', text('span', reason));
    if (hadFocus) document.querySelector('.dialog-close').focus();
  }

  function showDetails(app) {
    state.selected = app;
    $('dialog-title').textContent = app.name;
    $('detail-category').textContent = categoryLabel(app.category);
    $('detail-description').textContent = app.description;
    $('detail-host').textContent = app.host;
    $('detail-url').textContent = app.url;
    const notice = hasNotice(app) ? app.notice : '';
    $('detail-caution').hidden = !notice;
    $('detail-notice').hidden = !notice;
    $('detail-notice').textContent = notice;
    $('dialog-note').textContent = desktopApi
      ? copy('Compass asks for confirmation before opening this address in your default browser.', 'Compass adresi tarayıcıda açmadan önce onayını ister.')
      : copy('Open Compass for desktop to visit this website.', 'Bu siteyi açmak için Compass masaüstü uygulamasını kullan.');
    $('open-official').disabled = !desktopApi;
    $('detail-verification').hidden = false;
    $('verification-scope').hidden = false;
    $('dialog-status').textContent = '';
    $('blocked-destination').textContent = '';
    if (blocked.has(app.id)) showBlocked(blocked.get(app.id));
    $('app-dialog').showModal();
  }

  function updateFavoriteButton(button) {
    const id = button.dataset.favorite;
    const saved = favorites.has(id);
    button.disabled = favoritesStatus !== 'ready';
    button.setAttribute('aria-pressed', String(saved));
    if (pendingFavorites.has(id)) button.setAttribute('aria-disabled', 'true');
    else button.removeAttribute('aria-disabled');
    button.title = saved ? copy('Remove from favorites', 'Favorilerden çıkar') : copy('Save to favorites', 'Favorilere ekle');
  }

  function renderFavoritesStatus() {
    let message = '';
    if (state.view === 'favorites') {
      if (!desktop) {
        message = copy('Preview favorites clear when you reload or close this page.',
          'Önizlemedeki favoriler bu sayfayı yenileyince veya kapatınca silinir.');
      } else if (favoritesStatus === 'loading') {
        message = copy('Loading your favorites…', 'Favorilerin yükleniyor…');
      } else if (favoritesStatus === 'error') {
        message = copy('Compass could not read your favorites from this device.', 'Compass bu cihazdaki favorileri okuyamadı.');
      }
    }
    $('favorites-status').hidden = !message;
    $('favorites-message').textContent = message;
    $('retry-favorites').hidden = favoritesStatus !== 'error' || typeof desktopApi?.list_favorites !== 'function'
      || typeof desktopApi?.set_favorite !== 'function';
  }

  function withFavoritesTimeout(request) {
    let timer;
    const deadline = new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error('Favorites storage did not respond')), favoritesLimitMs);
    });
    return Promise.race([request, deadline]).finally(() => clearTimeout(timer));
  }

  async function loadFavorites() {
    const api = desktopApi;
    if (typeof api?.list_favorites !== 'function' || typeof api?.set_favorite !== 'function') {
      favoritesStatus = 'error';
      renderFavoritesStatus();
      return;
    }
    if (document.activeElement === $('retry-favorites')) $('page-title').focus();
    favoritesStatus = 'loading';
    renderFavoritesStatus();
    try {
      const result = await withFavoritesTimeout(api.list_favorites());
      if (result?.ok !== true || !Array.isArray(result.ids) || !result.ids.every(id => typeof id === 'string')) {
        throw new Error('Invalid favorites response');
      }
      const saved = new Set(result.ids);
      favorites.clear();
      state.apps.forEach(app => { if (saved.has(app.id)) favorites.add(app.id); });
      favoritesStatus = 'ready';
    } catch (_) {
      favoritesStatus = 'error';
    }
    if (state.view === 'favorites') render();
    else $('cards').querySelectorAll('[data-favorite]').forEach(updateFavoriteButton);
  }

  function renderAfterFavoriteChange(id) {
    const active = document.activeElement;
    const activeCard = active.closest('.card');
    const removedCard = activeCard?.dataset.appId === id && !favorites.has(id);
    const target = removedCard ? activeCard.nextElementSibling || activeCard.previousElementSibling : activeCard;
    const targetId = target?.dataset.appId;
    const selector = active.matches('[data-favorite]') ? '[data-favorite]' : '.details-button';
    render();
    if (activeCard) {
      const targetCard = targetId ? $('cards').querySelector(`[data-app-id="${CSS.escape(targetId)}"]`) : null;
      const emptyAction = $('favorites-empty').hidden ? $('search') : $('browse-favorites');
      (targetCard?.querySelector(selector) || emptyAction).focus({ preventScroll: Boolean(targetCard) });
    } else if (active === $('browse-favorites') && $('favorites-empty').hidden) {
      $('search').focus();
    }
  }

  async function toggleFavorite(button) {
    const id = button.dataset.favorite;
    if (favoritesStatus !== 'ready' || pendingFavorites.has(id)) return;
    const save = !favorites.has(id);
    pendingFavorites.add(id);
    updateFavoriteButton(button);
    let changed = false;
    try {
      if (desktop) {
        const result = await withFavoritesTimeout(desktopApi.set_favorite(id, save));
        if (result?.ok !== true || result.saved !== save) throw new Error('Invalid favorite update response');
      }
      if (save) favorites.add(id);
      else favorites.delete(id);
      changed = true;
    } catch (_) {
      notify(copy('Could not update your favorites. Try again.', 'Favoriler güncellenemedi. Tekrar dene.'));
    } finally {
      pendingFavorites.delete(id);
      if (changed && state.view === 'favorites') renderAfterFavoriteChange(id);
      else {
        const visibleButton = $('cards').querySelector(`[data-favorite="${CSS.escape(id)}"]`);
        if (visibleButton) updateFavoriteButton(visibleButton);
      }
    }
  }

  function render() {
    $('clear-search').hidden = !state.query;
    document.querySelectorAll('.filter').forEach(button => {
      const active = button.dataset.category === state.category;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    const terms = normalizeSearch(state.query).match(/\S+/g) || [];
    $('clear-filters').hidden = !terms.length && state.category === all && state.sort === 'featured';
    const onlyFavorites = state.view === 'favorites';
    const apps = state.apps.filter(app => (!onlyFavorites || favorites.has(app.id))
      && (state.category === all || app.category === state.category)
      && terms.every(term => app.searchText.includes(term)));
    if (state.sort === 'az') apps.sort((a, b) => a.name.localeCompare(b.name, document.documentElement.lang));
    else if (state.sort === 'recent') apps.reverse();
    else if (terms.length) {
      const phrase = terms.join(' ');
      const relevance = app => {
        if (app.searchName === phrase || app.host.toLowerCase() === phrase) return 0;
        if (app.searchName.startsWith(phrase)) return 1;
        return terms.some(term => app.searchName.includes(term)) ? 2 : 3;
      };
      apps.sort((a, b) => relevance(a) - relevance(b));
    }
    const cards = document.createDocumentFragment();
    apps.forEach(app => {
      const card = text('article', '', 'card');
      card.dataset.appId = app.id;
      const heading = text('div', '', 'card-heading');
      const title = text('div', '', 'card-title');
      title.append(text('h3', app.name), text('span', categoryLabel(app.category), 'category'));
      const favorite = text('button', '', 'favorite-toggle');
      favorite.type = 'button';
      favorite.dataset.favorite = app.id;
      favorite.setAttribute('aria-label', copy(`${app.name} favorite`, `${app.name} favori durumu`));
      updateFavoriteButton(favorite);
      heading.append(title, favorite);
      const bottom = text('div', '', 'card-bottom');
      const publisher = text('div', '', 'publisher');
      const address = text('div', '', 'publisher-address');
      const source = text('span', app.host, 'source');
      source.title = app.url;
      const label = document.createElement('span');
      updatePublisherLabel(label, blocked.has(app.id));
      address.append(source, label);
      publisher.append(address);
      if (hasNotice(app)) publisher.append(text('span', copy('Caution', 'Dikkat'), 'security-label security-label--caution'));
      const button = text('button', copy('Details', 'Ayrıntılar'), 'details-button');
      button.setAttribute('aria-label', copy(`Details for ${app.name}`, `${app.name} ayrıntıları`));
      bottom.append(publisher, button);
      const description = text('p', app.description, 'card-description');
      description.lang = 'en';
      card.append(heading, description, bottom);
      cards.append(card);
    });
    $('cards').replaceChildren(cards);
    const favoritesEmpty = onlyFavorites && favoritesStatus === 'ready' && favorites.size === 0;
    $('favorites-empty').hidden = !favoritesEmpty;
    $('empty').hidden = apps.length !== 0 || favoritesEmpty || (onlyFavorites && favoritesStatus !== 'ready');
    renderFavoritesStatus();
    const count = apps.length.toLocaleString(document.documentElement.lang);
    $('result-count').hidden = onlyFavorites && favoritesStatus !== 'ready';
    $('result-count').textContent = copy(`${count} ${apps.length === 1 ? 'app' : 'apps'}`, `${count} uygulama`);
    const allEntries = onlyFavorites ? copy('Saved apps', 'Kaydedilen uygulamalar') : copy('All entries', 'Tüm kayıtlar');
    const category = state.category === all ? allEntries : categoryLabel(state.category);
    $('results-title').textContent = terms.length ? copy('Search results', 'Arama sonuçları') : category;
  }

  function showCatalog(apps) {
    if (!Array.isArray(apps) || !apps.length) throw new Error('Invalid app catalog');
    const entries = Array.from(apps);
    const validEntries = entries.every(app => app
      && catalogFields.every(field => typeof app[field] === 'string' && app[field].trim())
      && Array.isArray(app.tags) && app.tags.every(tag => typeof tag === 'string'));
    if (!validEntries || new Set(entries.map(app => app.id)).size !== entries.length) throw new Error('Invalid app catalog');

    const moveFocus = document.activeElement === $('catalog-loading');
    state.apps = entries.map(app => ({
      ...app,
      searchName: normalizeSearch(app.name),
      searchText: normalizeSearch([app.id, app.name, app.category, turkishCategories.get(app.category),
        app.description, app.host, app.url, ...app.tags, ...app.tags.map(tag => turkishTags.get(tag))].join(' ')),
    }));
    const categories = [all, ...new Set(entries.map(app => app.category))];
    $('filters').replaceChildren();
    categories.forEach(category => {
      const button = text('button', categoryLabel(category), 'filter');
      button.dataset.category = category;
      button.addEventListener('click', () => {
        state.category = category;
        render();
      });
      $('filters').append(button);
    });
    render();
    setCatalogView('ready');
    if (moveFocus) $('search').focus();
  }

  function showCatalogError(english, turkish) {
    const moveFocus = document.activeElement === $('catalog-loading');
    catalogError = [english, turkish];
    updateStartupCopy();
    setCatalogView('error');
    if (moveFocus && !$('retry-catalog').hidden) $('retry-catalog').focus();
  }

  function desktopBridge() {
    const api = window.pywebview?.api;
    return typeof api?.catalog === 'function' && typeof api?.open_official === 'function' ? api : null;
  }

  function finishCatalogAttempt(attempt) {
    if (catalogAttempt !== attempt) return false;
    clearTimeout(attempt.deadline);
    clearInterval(attempt.bridgePoll);
    catalogAttempt = null;
    return true;
  }

  async function requestDesktopCatalog() {
    const attempt = catalogAttempt;
    if (!attempt || attempt.requested) return;
    const api = desktopBridge();
    if (!api) return;

    attempt.requested = true;
    clearInterval(attempt.bridgePoll);
    updateStartupCopy();
    renderLinkCheck();
    try {
      const apps = await api.catalog();
      if (catalogAttempt !== attempt) return;
      showCatalog(apps);
    } catch (_) {
      if (finishCatalogAttempt(attempt)) {
        showCatalogError('Compass couldn’t read the catalog. Try again, then restart Compass if the problem continues.',
          'Compass kataloğu okuyamadı. Tekrar dene. Sorun sürerse Compass’ı yeniden başlat.');
      }
      return;
    }

    finishCatalogAttempt(attempt);
    desktopApi = api;
    $('suggest-link').hidden = typeof api.suggest_link !== 'function';
    loadFavorites();
    if (typeof api.app_info === 'function') {
      try {
        const { version } = await api.app_info();
        if (typeof version === 'string' && version) $('app-version').textContent = version;
      } catch (_) {
        // The catalog and link confirmation remain usable if version metadata is unavailable.
      }
    }
  }

  function loadDesktopCatalog() {
    if (catalogAttempt || desktopApi) return;
    const attempt = { requested: false };
    catalogAttempt = attempt;
    const moveFocus = document.activeElement === $('retry-catalog');
    updateStartupCopy();
    setCatalogView('loading');
    if (moveFocus) $('catalog-loading').focus();

    attempt.deadline = setTimeout(() => {
      if (!finishCatalogAttempt(attempt)) return;
      if (attempt.requested) {
        showCatalogError('The desktop connection didn’t return the catalog in time. Select Retry to try again.',
          'Katalog zamanında yanıt vermedi. Tekrar dene düğmesine bas.');
      } else {
        showCatalogError('Compass couldn’t connect to the desktop window. Select Retry to try again.',
          'Compass masaüstü uygulamasına bağlanamadı. Tekrar dene düğmesine bas.');
      }
    }, startupLimitMs);
    // Some renderers expose the bridge without delivering a readiness event to this page.
    attempt.bridgePoll = setInterval(requestDesktopCatalog, 100);
    requestDesktopCatalog();
  }

  $('search').addEventListener('input', event => { state.query = event.target.value; render(); });
  $('clear-search').addEventListener('click', () => {
    state.query = $('search').value = '';
    render();
    $('search').focus();
  });
  $('sort').addEventListener('change', event => { state.sort = event.target.value; render(); });
  $('layout-picker').querySelectorAll('button').forEach(button => {
    button.addEventListener('click', () => applyLayout(button.dataset.layout));
  });
  $('language').addEventListener('change', event => {
    const language = event.target.value;
    applyLanguage(language);
    try { localStorage.setItem(languageKey, language); } catch (_) { /* Current session still uses the selected language. */ }
  });
  $('reset').addEventListener('click', () => { reset(); $('search').focus(); });
  $('clear-filters').addEventListener('click', () => { reset(); $('search').focus(); });
  $('cards').addEventListener('click', event => {
    const favorite = event.target.closest('[data-favorite]');
    if (favorite) {
      toggleFavorite(favorite);
      return;
    }
    const card = event.target.closest('.details-button')?.closest('.card');
    if (!card) return;
    const app = state.apps.find(entry => entry.id === card.dataset.appId);
    if (app) showDetails(app);
  });
  document.querySelectorAll('.nav').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
  document.querySelector('.brand').addEventListener('click', event => { event.preventDefault(); reset(); setView('discover'); });
  $('trust-details').addEventListener('click', () => setView('privacy'));
  $('quick-check').addEventListener('click', () => {
    setView('checker');
    if (!$('link-address').disabled) $('link-address').focus();
  });
  $('back-discover').addEventListener('click', () => setView('discover'));
  $('browse-favorites').addEventListener('click', () => { setView('discover'); $('search').focus(); });
  $('retry-favorites').addEventListener('click', loadFavorites);
  $('link-address').addEventListener('input', () => {
    linkCheck = {};
    renderLinkCheck();
  });
  $('link-check-form').addEventListener('submit', inspectLink);
  $('explain-link').addEventListener('click', explainLink);
  $('retry-catalog').addEventListener('click', loadDesktopCatalog);
  $('suggest-link').addEventListener('click', async event => {
    const button = event.currentTarget;
    if (button.hidden || button.hasAttribute('aria-disabled')) return;
    button.setAttribute('aria-disabled', 'true');
    const errorMessage = copy('Could not open the suggestion form. Try again.', 'Öneri formu açılamadı. Tekrar dene.');
    try {
      const response = await desktopApi.suggest_link();
      if (response?.ok === true) notify(copy(response.message || 'Opened the GitHub suggestion form.', 'GitHub öneri formu açıldı.'));
      else notify(response?.message ? bridgeMessage(response.message) : errorMessage);
    } catch (_) {
      notify(errorMessage);
    } finally {
      button.removeAttribute('aria-disabled');
    }
  });
  document.querySelector('.dialog-close').addEventListener('click', () => { if (!state.busy) $('app-dialog').close(); });
  $('app-dialog').addEventListener('cancel', event => { if (state.busy) event.preventDefault(); });
  $('app-dialog').addEventListener('keydown', event => {
    if (state.busy && event.key === 'Escape') event.preventDefault();
  });
  $('open-official').addEventListener('click', async () => {
    if (state.busy || !state.selected || !desktopApi || blocked.has(state.selected.id)) return;
    const openButton = $('open-official');
    const closeButton = document.querySelector('.dialog-close');
    state.busy = true;
    openButton.setAttribute('aria-disabled', 'true');
    closeButton.setAttribute('aria-disabled', 'true');
    $('dialog-status').textContent = copy('Waiting for confirmation…', 'Onay bekleniyor…');
    try {
      const response = await desktopApi.open_official(state.selected.id);
      const message = typeof response?.message === 'string' ? response.message : '';
      if (response?.status === 'blocked') {
        blocked.set(state.selected.id, message);
        showBlocked(message);
      } else if (response?.ok === true) {
        $('app-dialog').close();
        notify(copy(message || 'Opened the publisher website.', 'Yayıncının adresi tarayıcıya gönderildi.'));
      } else {
        $('dialog-status').textContent = message ? bridgeMessage(message) : copy('Could not open the website. Try again.', 'Site açılamadı. Tekrar dene.');
      }
    } catch (_) {
      $('dialog-status').textContent = copy('The desktop connection is unavailable. Restart Compass to try again.',
        'Masaüstü bağlantısı kesildi. Yeniden denemek için Compass’ı başlat.');
    } finally {
      state.busy = false;
      openButton.removeAttribute('aria-disabled');
      closeButton.removeAttribute('aria-disabled');
    }
  });

  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      if ($('app-dialog').open) return;
      if (state.view === 'privacy' || state.view === 'checker') setView('discover');
      if (!$('catalog-results').hidden) $('search').focus();
      else if (!$('catalog-loading').hidden) $('catalog-loading').focus();
      else if (!$('load-error').hidden && !$('retry-catalog').hidden) $('retry-catalog').focus();
    }
  });

  applyLanguage(preferredLanguage());
  if (desktop) {
    window.addEventListener('pywebviewready', () => {
      renderLinkCheck();
      if (catalogAttempt) requestDesktopCatalog();
      else if (desktopBridge()) loadDesktopCatalog();
    });
    loadDesktopCatalog();
  } else {
    try {
      showCatalog(window.COMPASS_CATALOG);
    } catch (_) {
      $('retry-catalog').hidden = true;
      showCatalogError('Keep index.html and its bundled assets in the same folder, then reload this page.',
        'index.html ile birlikte gelen dosyaları aynı klasörde tut ve bu sayfayı yeniden yükle.');
    }
  }
})();
