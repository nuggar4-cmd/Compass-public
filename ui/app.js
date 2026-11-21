'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const desktop = new URLSearchParams(window.location.search).get('desktop') === '1';
  const all = 'All apps';
  const catalogFields = ['id', 'name', 'category', 'description', 'host', 'url', 'glyph'];
  const startupLimitMs = 8000;
  const state = { apps: [], category: all, query: '', sort: 'featured', view: 'discover', selected: null, busy: false };
  const blocked = new Map();
  let desktopApi;
  let catalogAttempt;
  let toastTimer;

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
    return value.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase();
  }

  function setCatalogView(view) {
    $('discover-page').classList.toggle('startup-layout', desktop && view !== 'ready');
    $('catalog-loading').hidden = view !== 'loading';
    $('load-error').hidden = view !== 'error';
    $('catalog-results').hidden = view !== 'ready';
  }

  function setLoadingCopy(title, detail) {
    $('catalog-loading-title').textContent = title;
    $('catalog-loading-detail').textContent = detail;
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
    $('page-title').textContent = view === 'privacy' ? 'Privacy & trust' : view === 'library' ? all : 'Discover';
    document.querySelector('.hero').hidden = view === 'library';
    $('library-title').hidden = view !== 'library';
    if (view === 'library') reset();
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
    label.textContent = isBlocked ? 'Blocked' : 'Verified publisher';
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
    $('dialog-note').textContent = 'Choose another listing to visit a website.';
    const openButton = $('open-official');
    const hadFocus = document.activeElement === openButton;
    openButton.disabled = true;
    const label = text('strong', 'Blocked', 'security-label security-label--blocked');
    $('dialog-status').textContent = '';
    $('blocked-destination').replaceChildren(label, ' ', text('span', message));
    if (hadFocus) document.querySelector('.dialog-close').focus();
  }

  function showDetails(app) {
    state.selected = app;
    $('dialog-title').textContent = app.name;
    $('detail-icon').textContent = app.glyph;
    $('detail-icon').className = `app-icon app-${app.id}`;
    $('detail-category').textContent = app.category;
    $('detail-description').textContent = app.description;
    $('detail-host').textContent = app.host;
    $('detail-url').textContent = app.url;
    const notice = hasNotice(app) ? app.notice : '';
    $('detail-notice').hidden = !notice;
    $('detail-notice').textContent = notice;
    $('dialog-note').textContent = desktopApi
      ? 'Compass asks for confirmation before opening this address in your default browser.'
      : 'Open Compass for desktop to visit this website.';
    $('open-official').disabled = !desktopApi;
    $('detail-verification').hidden = false;
    $('verification-scope').hidden = false;
    $('dialog-status').textContent = '';
    $('blocked-destination').textContent = '';
    if (blocked.has(app.id)) showBlocked(blocked.get(app.id));
    $('app-dialog').showModal();
  }

  function render() {
    document.querySelectorAll('.filter').forEach(button => {
      const active = button.dataset.category === state.category;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    const terms = normalizeSearch(state.query).match(/\S+/g) || [];
    const apps = state.apps.filter(app => (state.category === all || app.category === state.category)
      && terms.every(term => app.searchText.includes(term)));
    if (state.sort === 'az') apps.sort((a, b) => a.name.localeCompare(b.name, 'en'));
    const cards = document.createDocumentFragment();
    apps.forEach(app => {
      const card = text('article', '', 'card');
      card.dataset.appId = app.id;
      const heading = text('div', '', 'card-heading');
      const icon = text('span', app.glyph, `app-icon app-${app.id}`);
      icon.setAttribute('aria-hidden', 'true');
      heading.append(icon);
      const identity = document.createElement('div');
      identity.append(text('h3', app.name), text('span', app.category, 'category'));
      heading.append(identity);
      const bottom = text('div', '', 'card-bottom');
      const publisher = text('div', '', 'publisher');
      const badges = text('div', '', 'publisher-badges');
      const label = document.createElement('span');
      updatePublisherLabel(label, blocked.has(app.id));
      badges.append(label);
      if (hasNotice(app)) badges.append(text('span', 'Caution', 'security-label security-label--caution'));
      const source = text('span', app.host, 'source');
      source.title = app.url;
      publisher.append(badges, source);
      const button = text('button', 'Details', 'details-button');
      button.setAttribute('aria-label', `Details for ${app.name}`);
      button.addEventListener('click', () => showDetails(app));
      bottom.append(publisher, button);
      card.append(heading, text('p', app.description, 'card-description'), bottom);
      cards.append(card);
    });
    $('cards').replaceChildren(cards);
    $('empty').hidden = apps.length !== 0;
    $('result-count').textContent = `${apps.length} ${apps.length === 1 ? 'app' : 'apps'}`;
    $('results-title').textContent = terms.length ? 'Search results' : state.category !== all ? state.category : 'App catalog';
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
      searchText: normalizeSearch([app.id, app.name, app.category, app.description, app.host, app.url, ...app.tags].join(' ')),
    }));
    const categories = [all, ...new Set(entries.map(app => app.category))];
    $('filters').replaceChildren();
    categories.forEach(category => {
      const button = text('button', category, 'filter');
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

  function showCatalogError(message) {
    const moveFocus = document.activeElement === $('catalog-loading');
    $('load-error-message').textContent = message;
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
    setLoadingCopy('Loading the app catalog…', 'Reading the publisher addresses stored with Compass.');
    try {
      const apps = await api.catalog();
      if (catalogAttempt !== attempt) return;
      showCatalog(apps);
    } catch (_) {
      if (finishCatalogAttempt(attempt)) showCatalogError('Compass couldn’t read the catalog. Try again, then restart Compass if the problem continues.');
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
    setLoadingCopy('Connecting to Compass…', 'Waiting for the desktop window to respond.');
    setCatalogView('loading');
    if (moveFocus) $('catalog-loading').focus();

    attempt.deadline = setTimeout(() => {
      if (!finishCatalogAttempt(attempt)) return;
      const message = attempt.requested
        ? 'The desktop connection didn’t return the catalog in time. Select Retry to try again.'
        : 'Compass couldn’t connect to the desktop window. Select Retry to try again.';
      showCatalogError(message);
    }, startupLimitMs);
    // Some renderers expose the bridge without delivering a readiness event to this page.
    attempt.bridgePoll = setInterval(requestDesktopCatalog, 100);
    requestDesktopCatalog();
  }

  $('search').addEventListener('input', event => { state.query = event.target.value; render(); });
  $('sort').addEventListener('change', event => { state.sort = event.target.value; render(); });
  $('reset').addEventListener('click', () => { reset(); $('search').focus(); });
  document.querySelectorAll('.nav').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
  document.querySelector('.brand').addEventListener('click', event => { event.preventDefault(); reset(); setView('discover'); });
  $('trust-details').addEventListener('click', () => setView('privacy'));
  $('back-discover').addEventListener('click', () => setView('discover'));
  $('retry-catalog').addEventListener('click', loadDesktopCatalog);
  $('suggest-link').addEventListener('click', async event => {
    const button = event.currentTarget;
    if (button.hidden || button.hasAttribute('aria-disabled')) return;
    button.setAttribute('aria-disabled', 'true');
    const errorMessage = 'Could not open the suggestion form. Try again.';
    try {
      const response = await desktopApi.suggest_link();
      notify(response?.message || errorMessage);
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
    $('dialog-status').textContent = 'Waiting for confirmation…';
    try {
      const response = await desktopApi.open_official(state.selected.id);
      const message = typeof response?.message === 'string' ? response.message : '';
      if (response?.status === 'blocked') {
        const reason = message || 'The destination did not pass Compass’s catalog checks.';
        blocked.set(state.selected.id, reason);
        showBlocked(reason);
      } else if (response?.ok === true) {
        $('app-dialog').close();
        notify(message || 'Opened the publisher website.');
      } else {
        $('dialog-status').textContent = message || 'Could not open the website. Try again.';
      }
    } catch (_) {
      $('dialog-status').textContent = 'The desktop connection is unavailable. Restart Compass to try again.';
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
      showCatalogError('Keep index.html and its bundled assets in the same folder, then reload this page.');
    }
  }
})();
