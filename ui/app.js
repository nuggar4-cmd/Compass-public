'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const desktop = new URLSearchParams(window.location.search).get('desktop') === '1';
  const all = 'All apps';
  const state = { apps: [], category: all, query: '', sort: 'featured', view: 'discover', selected: null, busy: false };
  let desktopApi;
  let connecting = false;
  let startupTimer;
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

  function showDetails(app) {
    state.selected = app;
    $('dialog-title').textContent = app.name;
    $('detail-icon').textContent = app.glyph;
    $('detail-icon').className = `app-icon app-${app.id}`;
    $('detail-category').textContent = app.category;
    $('detail-description').textContent = app.description;
    $('detail-host').textContent = app.host;
    $('detail-url').textContent = app.url;
    $('dialog-note').textContent = desktopApi
      ? 'Compass asks for confirmation before opening this address in your default browser.'
      : 'Open Compass for desktop to visit this website.';
    $('open-official').disabled = !desktopApi;
    $('dialog-status').textContent = '';
    $('app-dialog').showModal();
  }

  function render() {
    document.querySelectorAll('.filter').forEach(button => {
      const active = button.dataset.category === state.category;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    const query = state.query.trim().toLocaleLowerCase('en');
    const apps = state.apps.filter(app => (state.category === all || app.category === state.category)
      && [app.name, app.category, app.description, ...app.tags].join(' ').toLocaleLowerCase('en').includes(query));
    if (state.sort === 'az') apps.sort((a, b) => a.name.localeCompare(b.name, 'en'));
    $('cards').replaceChildren();
    apps.forEach(app => {
      const card = text('article', '', 'card');
      const heading = text('div', '', 'card-heading');
      const icon = text('span', app.glyph, `app-icon app-${app.id}`);
      icon.setAttribute('aria-hidden', 'true');
      heading.append(icon);
      const identity = document.createElement('div');
      identity.append(text('h3', app.name), text('span', app.category, 'category'));
      heading.append(identity);
      const bottom = text('div', '', 'card-bottom');
      const source = text('span', app.host, 'source');
      source.title = app.url;
      const button = text('button', 'View app  ↗', 'details-button');
      button.setAttribute('aria-label', `View ${app.name}`);
      button.addEventListener('click', () => showDetails(app));
      bottom.append(source, button);
      card.append(heading, text('p', app.description, 'card-description'), bottom);
      $('cards').append(card);
    });
    $('empty').hidden = apps.length !== 0;
    $('result-count').textContent = `${apps.length} ${apps.length === 1 ? 'app' : 'apps'}`;
    $('results-title').textContent = query ? 'Search results' : state.category !== all ? state.category : 'App catalog';
  }

  function showCatalog(apps) {
    if (!Array.isArray(apps) || !apps.length) throw new Error('Catalog unavailable');
    const moveFocus = document.activeElement === $('catalog-loading');
    state.apps = apps;
    const categories = [all, ...new Set(apps.map(app => app.category))];
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
    $('nav-count').textContent = String(apps.length);
    $('nav-count').hidden = false;
    $('load-error').hidden = true;
    $('catalog-loading').hidden = true;
    $('catalog-results').hidden = false;
    render();
    if (moveFocus) $('search').focus();
  }

  function showCatalogError() {
    const moveFocus = document.activeElement === $('catalog-loading');
    $('catalog-loading').hidden = true;
    $('load-error').hidden = false;
    if (moveFocus) $('retry-catalog').focus();
  }

  async function loadDesktopCatalog() {
    if (connecting || desktopApi) return;
    const moveFocus = document.activeElement === $('retry-catalog');
    $('load-error').hidden = true;
    $('catalog-loading').hidden = false;
    if (moveFocus) $('catalog-loading').focus();
    clearTimeout(startupTimer);
    const api = window.pywebview?.api;
    if (typeof api?.catalog !== 'function' || typeof api?.open_official !== 'function') {
      startupTimer = setTimeout(showCatalogError, 6000);
      return;
    }

    connecting = true;
    let responseTimer;
    try {
      const timeout = new Promise((_, reject) => {
        responseTimer = setTimeout(() => reject(new Error('Catalog timed out')), 6000);
      });
      const apps = await Promise.race([api.catalog(), timeout]);
      showCatalog(apps);
      desktopApi = api;
      $('suggest-link').hidden = typeof api.suggest_link !== 'function';
    } catch (_) {
      showCatalogError();
    } finally {
      clearTimeout(responseTimer);
      connecting = false;
    }

    if (desktopApi && typeof api.app_info === 'function') {
      try {
        const { version } = await api.app_info();
        if (typeof version === 'string' && version) $('app-version').textContent = version;
      } catch (_) {
        // The catalog and link confirmation remain usable if version metadata is unavailable.
      }
    }
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
    if (state.busy || !state.selected || !desktopApi) return;
    const openButton = $('open-official');
    const closeButton = document.querySelector('.dialog-close');
    state.busy = true;
    openButton.setAttribute('aria-disabled', 'true');
    closeButton.setAttribute('aria-disabled', 'true');
    $('dialog-status').textContent = 'Waiting for confirmation…';
    try {
      const response = await desktopApi.open_official(state.selected.id);
      if (response.ok) {
        $('app-dialog').close();
        notify(response.message);
      } else {
        $('dialog-status').textContent = response.message;
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
    }
  });

  if (desktop) {
    window.addEventListener('pywebviewready', loadDesktopCatalog);
    loadDesktopCatalog();
  } else {
    try {
      showCatalog(window.COMPASS_CATALOG);
    } catch (_) {
      $('load-error-message').textContent = 'Keep index.html and its bundled assets in the same folder, then reload this page.';
      $('retry-catalog').hidden = true;
      showCatalogError();
    }
  }
})();
