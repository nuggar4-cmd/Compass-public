'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const desktop = new URLSearchParams(window.location.search).get('desktop') === '1';
  const all = 'All apps';
  const catalogFields = ['id', 'name', 'category', 'description', 'host', 'url', 'glyph'];
  const startupLimitMs = 8000;
  const languageKey = 'compass-language';
  const turkishCategories = new Map([
    [all, 'Tümü'], ['Browsers', 'Tarayıcılar'], ['Development', 'Geliştirme'], ['Creative', 'Tasarım'],
    ['Utilities', 'Araçlar'], ['Media', 'Medya'], ['Productivity', 'Üretkenlik'], ['Gaming', 'Oyun'],
    ['Communication', 'İletişim'], ['Education', 'Eğitim'],
  ]);
  const turkishBridgeMessages = new Map([
    ['Opening cancelled.', 'Açma işlemi iptal edildi.'],
    ['A link request is already open.', 'Bir bağlantı açma isteği zaten bekliyor.'],
    ['Could not open your browser. Please try again.', 'Tarayıcı açılamadı. Lütfen tekrar dene.'],
    ['Could not open the website. Please try again.', 'Site açılamadı. Lütfen tekrar dene.'],
    ['Compass blocked this address because it did not pass the catalog check.', 'Bu adres katalog denetiminden geçmediği için engellendi.'],
  ]);
  const localizedText = Array.from(document.querySelectorAll('[data-tr]'), el => [el, el.textContent]);
  const localizedAttributes = [['data-tr-label', 'aria-label'], ['data-tr-placeholder', 'placeholder']]
    .flatMap(([translation, attribute]) => Array.from(document.querySelectorAll(`[${translation}]`),
      el => [el, attribute, el.getAttribute(attribute), el.getAttribute(translation)]));
  const state = { apps: [], category: all, query: '', sort: 'featured', view: 'discover', selected: null, busy: false };
  const blocked = new Map();
  let desktopApi;
  let catalogAttempt;
  let catalogError;
  let toastTimer;

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
    state.view = view;
    document.querySelectorAll('.nav').forEach(button => {
      const active = button.dataset.view === view;
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    $('privacy-page').hidden = view !== 'privacy';
    $('discover-page').hidden = view === 'privacy';
    updatePageTitle();
    document.querySelector('.hero').hidden = view === 'library';
    $('library-title').hidden = view !== 'library';
    window.scrollTo(0, 0);
    $('page-title').focus({ preventScroll: true });
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
    $('detail-icon').textContent = app.glyph;
    $('detail-icon').className = `app-icon app-${app.id}`;
    $('detail-category').textContent = categoryLabel(app.category);
    $('detail-description').textContent = app.description;
    $('detail-host').textContent = app.host;
    $('detail-url').textContent = app.url;
    const notice = hasNotice(app) ? app.notice : '';
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

  function render() {
    $('clear-search').hidden = !state.query;
    document.querySelectorAll('.filter').forEach(button => {
      const active = button.dataset.category === state.category;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    const terms = normalizeSearch(state.query).match(/\S+/g) || [];
    const apps = state.apps.filter(app => (state.category === all || app.category === state.category)
      && terms.every(term => app.searchText.includes(term)));
    if (state.sort === 'az') apps.sort((a, b) => a.name.localeCompare(b.name, document.documentElement.lang));
    const cards = document.createDocumentFragment();
    apps.forEach(app => {
      const card = text('article', '', 'card');
      card.dataset.appId = app.id;
      const heading = text('div', '', 'card-heading');
      const icon = text('span', app.glyph, `app-icon app-${app.id}`);
      icon.setAttribute('aria-hidden', 'true');
      heading.append(icon);
      const identity = document.createElement('div');
      identity.append(text('h3', app.name), text('span', categoryLabel(app.category), 'category'));
      heading.append(identity);
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
    $('empty').hidden = apps.length !== 0;
    const count = apps.length.toLocaleString(document.documentElement.lang);
    $('result-count').textContent = copy(`${count} ${apps.length === 1 ? 'app' : 'apps'}`, `${count} uygulama`);
    const category = state.category === all ? copy('App catalog', 'Uygulama kataloğu') : categoryLabel(state.category);
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
      searchText: normalizeSearch([app.id, app.name, app.category, turkishCategories.get(app.category),
        app.description, app.host, app.url, ...app.tags].join(' ')),
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
    $('nav-count').textContent = String(entries.length);
    $('nav-count').hidden = false;
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
  $('language').addEventListener('change', event => {
    const language = event.target.value;
    applyLanguage(language);
    try { localStorage.setItem(languageKey, language); } catch (_) { /* Current session still uses the selected language. */ }
  });
  $('reset').addEventListener('click', () => { reset(); $('search').focus(); });
  $('cards').addEventListener('click', event => {
    const card = event.target.closest('.details-button')?.closest('.card');
    if (!card) return;
    const app = state.apps.find(entry => entry.id === card.dataset.appId);
    if (app) showDetails(app);
  });
  document.querySelectorAll('.nav').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
  document.querySelector('.brand').addEventListener('click', event => { event.preventDefault(); reset(); setView('discover'); });
  $('trust-details').addEventListener('click', () => setView('privacy'));
  $('back-discover').addEventListener('click', () => setView('discover'));
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
      if (state.view === 'privacy') setView('discover');
      if (!$('catalog-results').hidden) $('search').focus();
      else if (!$('catalog-loading').hidden) $('catalog-loading').focus();
      else if (!$('load-error').hidden && !$('retry-catalog').hidden) $('retry-catalog').focus();
    }
  });

  applyLanguage(preferredLanguage());
  if (desktop) {
    window.addEventListener('pywebviewready', () => {
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
