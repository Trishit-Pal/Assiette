import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUpRight, Bookmark, Check, CheckCheck, ChevronDown, CircleHelp, Clock3, ExternalLink, Heart, Leaf, List, Map, MapPin, Menu, Moon, Search, ShieldCheck, ShoppingBasket, SlidersHorizontal, Smile, Sparkles, Sun, Utensils, Wallet, X } from 'lucide-react'
import { copy, places, type Category, type Copy, type Lang, type Place } from './lib/data'
import { Tilt } from './components/Tilt'

const ParisMap = lazy(() => import('./components/ParisMap'))

function useStored<T,>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(() => {
    try { const stored = localStorage.getItem(key); return stored ? JSON.parse(stored) as T : fallback } catch { return fallback }
  })
  useEffect(() => { try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* Storage may be disabled in private browsers. */ } }, [key, value])
  return [value, setValue] as const
}

function Brand({ small = false }: { small?: boolean }) {
  return <Link to="/" className={`brand ${small ? 'brand-small' : ''}`} aria-label="Assiette home">
    <span className="brand-mark"><Utensils size={21} strokeWidth={1.7} /><span className="brand-plate" /></span>
    <span>assiette<span className="brand-period">.</span></span>
  </Link>
}

function Modal({ children, title, onClose, wide = false }: { children: ReactNode; title: string; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  const closeRef = useRef(onClose)
  useEffect(() => { closeRef.current = onClose }, [onClose])
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const oldOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const timer = setTimeout(() => ref.current?.querySelector<HTMLElement>('button, input, a')?.focus(), 80)
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeRef.current()
      if (event.key === 'Tab') {
        const nodes = ref.current?.querySelectorAll<HTMLElement>('button, a[href], input, select, [tabindex="0"]')
        if (!nodes?.length) return
        const first = nodes[0], last = nodes[nodes.length - 1]
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', handler)
    return () => { clearTimeout(timer); document.body.style.overflow = oldOverflow; document.removeEventListener('keydown', handler); previous?.focus() }
  }, [])
  return <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
    <motion.div ref={ref} role="dialog" aria-modal="true" aria-label={title} className={`modal ${wide ? 'modal-wide' : ''}`} initial={{ opacity: 0, y: 30, rotateX: -5, scale: 0.97 }} animate={{ opacity: 1, y: 0, rotateX: 0, scale: 1 }} exit={{ opacity: 0, y: 15, scale: 0.98 }} transition={{ type: 'spring', damping: 28, stiffness: 280 }} onClick={event => event.stopPropagation()}>
      <button className="modal-close icon-button" onClick={onClose} aria-label="Close dialog"><X size={20} /></button>
      {children}
    </motion.div>
  </motion.div>
}

function Hero({ t }: { t: Copy }) {
  const reduced = useReducedMotion()
  return <section className="hero container" aria-labelledby="hero-title">
    <motion.div className="hero-copy" initial={reduced ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
      <div className="eyebrow"><span className="location-dot" />{t.location}<span className="eyebrow-line" /></div>
      <h1 id="hero-title">{t.heroLine1}<br /><span>{t.heroLine2}</span><svg className="title-spark" width="36" height="45" viewBox="0 0 36 45" aria-hidden="true"><path d="M7 28 4 8M17 25 25 4M23 34l11-9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /></svg></h1>
      <p className="hero-intro">{t.heroBody}</p>
      <p className="hero-description">{t.heroBody2}</p>
      <div className="hero-actions"><a href="#discover" className="button button-primary">{t.explore}<ArrowUpRight size={19} /></a><Link to="/about" className="text-link">{t.how}<ArrowRight size={16} /></Link></div>
      <div className="student-note"><div className="student-faces" aria-hidden="true"><span>☺</span><span>☺</span><span>☺</span></div><div><strong>{t.students}</strong><span>{t.noFees}</span></div><svg className="little-arrow" width="45" height="31" viewBox="0 0 45 31" aria-hidden="true"><path d="M40 3c2 22-26 27-36 15m0 0 3 11M4 18l11 1" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg></div>
    </motion.div>
    <div className="hero-art" aria-label="A floating three-dimensional plate of pasta, tomatoes, and basil">
      <div className="hero-glow" />
      <svg className="orbit orbit-back" viewBox="0 0 620 400" aria-hidden="true"><ellipse cx="310" cy="200" rx="282" ry="134" fill="none" stroke="currentColor" strokeDasharray="3 7" /></svg>
      <div className="plate-floor-shadow" />
      <Tilt className="plate-interaction" strength={12}><div className="floating-plate"><img src="/images/hero-plate.webp" alt="An abundant ceramic plate of rigatoni with roasted tomatoes, basil, and avocado" fetchPriority="high" width={1024} height={1024} /></div></Tilt>
      <div className="floating-leaf leaf-one" aria-hidden="true"><span /></div><div className="floating-leaf leaf-two" aria-hidden="true"><span /></div>
      <div className="floating-tomato" aria-hidden="true"><span>✦</span></div>
      <span className="art-spark spark-one" aria-hidden="true">✧</span><span className="art-spark spark-two" aria-hidden="true">✦</span><span className="art-dot" />
      <div className="price-ticket"><div className="ticket-top"><span>{t.from}</span><Utensils size={16} /></div><div className="ticket-price">1<span>€</span><span className="ticket-star" aria-hidden="true">✳</span></div><div className="ticket-bottom"><span>{t.studentPrice}</span><Heart size={13} /></div></div>
      <div className="plate-caption"><svg width="50" height="48" viewBox="0 0 50 48" aria-hidden="true"><path d="M5 3c-1 32 26 34 37 20m0 0-11 1m11-1-2 11" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg><span>{t.plateLabel}</span></div>
      <span className="art-coordinate">48.8566° N &nbsp; 2.3522° E</span>
    </div>
  </section>
}

function TrustStrip({ t }: { t: Copy }) {
  return <section className="trust-strip container" aria-label="The Assiette promise">
    <div><span className="trust-icon"><ShieldCheck size={24} strokeWidth={1.5} /></span><p><strong>{t.official}</strong><span>{t.officialSub}</span></p></div>
    <div><span className="trust-icon"><Wallet size={24} strokeWidth={1.5} /></span><p><strong>{t.budget}</strong><span>{t.budgetSub}</span></p></div>
    <div><span className="trust-icon"><Heart size={24} strokeWidth={1.5} /></span><p><strong>{t.community}</strong><span>{t.communitySub}</span></p></div>
  </section>
}

function PlaceCard({ place, t, lang, saved, onSave, onSelect }: { place: Place; t: Copy; lang: Lang; saved: boolean; onSave: () => void; onSelect: () => void }) {
  return <Tilt className="place-card" strength={4}>
    <div className="place-photo"><button className="photo-button" onClick={onSelect} aria-label={`${t.details}: ${place.name}`}><img src={place.image} alt={place.imageAlt} loading="lazy" /></button>
      <span className={`place-category ${place.category === 'distribution' ? 'category-green' : ''}`}>{place.category === 'crous' ? <Utensils size={12} /> : <ShoppingBasket size={13} />}{place.category === 'crous' ? t.mealTag : t.basketTag}</span>
      <button className={`save-button ${saved ? 'is-saved' : ''}`} onClick={onSave} aria-label={`${saved ? t.unsave : t.save}: ${place.name}`} aria-pressed={saved}><Bookmark size={17} fill={saved ? 'currentColor' : 'none'} /></button>
      <span className="photo-price">{place.price ? <>1€ <small>{t.perMeal}</small></> : <>{t.free}<Leaf size={14} /></>}</span>
    </div>
    <div className="place-content"><div className="place-area"><MapPin size={12} /><span>{lang === 'en' ? place.area : place.areaFr}</span></div><button className="place-name" onClick={onSelect}>{place.name}<ArrowUpRight size={18} /></button><p className="place-description">{lang === 'en' ? place.description : place.descriptionFr}</p><div className="card-rule" /><div className="place-footer"><span><Clock3 size={13} />{place.category === 'crous' ? t.schedule : t.registration}</span><button aria-label={`${t.details}: ${place.name}`} onClick={onSelect}><ArrowRight size={17} /></button></div></div>
  </Tilt>
}

function Directory({ t, lang, saved, onSave, onSelect, savedOnly = false }: { t: Copy; lang: Lang; saved: string[]; onSave: (id: string) => void; onSelect: (place: Place) => void; savedOnly?: boolean }) {
  const [category, setCategory] = useState<Category>('all')
  const [query, setQuery] = useState('')
  const [district, setDistrict] = useState('all')
  const [price, setPrice] = useState('all')
  const [sort, setSort] = useState('recommended')
  const [view, setView] = useState<'list' | 'map'>('list')
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const reset = () => { setCategory('all'); setQuery(''); setDistrict('all'); setPrice('all'); setSort('recommended') }
  const results = useMemo(() => {
    const filtered = places.filter(place => (!savedOnly || saved.includes(place.id)) && (category === 'all' || place.category === category) && (district === 'all' || place.district === district || place.district === 'all') && (price === 'all' || place.price === Number(price)) && `${place.name} ${place.area} ${place.areaFr}`.toLowerCase().includes(query.toLowerCase().trim()))
    return sort === 'alphabetical' ? filtered.sort((a, b) => a.name.localeCompare(b.name)) : filtered
  }, [category, query, district, price, sort, savedOnly, saved])
  const visible = expanded || category !== 'all' || query || district !== 'all' || price !== 'all' || savedOnly ? results : results.slice(0, 3)
  const activeFilters = Number(price !== 'all') + Number(sort !== 'recommended')
  return <section id="discover" className={`directory container ${savedOnly ? 'saved-directory' : ''}`} aria-labelledby="directory-title">
    <div className="section-heading"><div>{savedOnly && <span className="eyebrow"><Bookmark size={15} /> YOUR COLLECTION</span>}<h2 id="directory-title">{savedOnly ? t.savedTitle : t.heading}<span className="heading-dot">.</span></h2><p>{savedOnly ? t.savedSubtitle : t.subtitle}</p></div><div className="view-toggle" aria-label={lang === 'en' ? 'View mode' : 'Mode d’affichage'}><button className={view === 'list' ? 'active' : ''} onClick={() => setView('list')} aria-pressed={view === 'list'}><List size={16} />{t.list}</button><button className={view === 'map' ? 'active' : ''} onClick={() => setView('map')} aria-pressed={view === 'map'}><Map size={16} />{t.map}</button></div></div>
    {(!savedOnly || saved.length > 0) && <><div className="directory-toolbar"><div className="category-tabs" aria-label="Meal type">{(['all', 'crous', 'distribution'] as Category[]).map(cat => <button key={cat} className={category === cat ? 'active' : ''} onClick={() => { setCategory(cat); setExpanded(false) }} aria-pressed={category === cat}>{cat === 'all' ? <Sparkles size={15} /> : cat === 'crous' ? <Utensils size={15} /> : <ShoppingBasket size={15} />}{t[cat]}<span className="tab-count">{places.filter(place => (cat === 'all' || place.category === cat) && (!savedOnly || saved.includes(place.id))).length}</span></button>)}</div><span className="results-count">{results.length} {t.options}<span className="count-dot" /></span></div>
    <div className="search-row"><label className="search-input"><Search size={18} /><input type="search" placeholder={t.search} value={query} onChange={event => setQuery(event.target.value)} aria-label={t.search} />{query && <button className="clear-search" onClick={() => setQuery('')} aria-label={t.reset}><X size={16} /></button>}</label><label className="district-select"><MapPin size={17} /><select value={district} onChange={event => setDistrict(event.target.value)} aria-label={t.allParis}><option value="all">{t.allParis}</option><option value="5">{lang === 'en' ? '5th arrondissement' : '5e arrondissement'}</option><option value="6">{lang === 'en' ? '6th arrondissement' : '6e arrondissement'}</option></select><ChevronDown size={15} /></label><button className={`filter-button ${activeFilters ? 'has-filters' : ''}`} onClick={() => setFiltersOpen(true)}><SlidersHorizontal size={16} />{t.filters}{activeFilters > 0 && <span>{activeFilters}</span>}</button></div></>}
    {results.length === 0 ? <div className="empty-state"><span className="empty-icon">{savedOnly && !saved.length ? <Bookmark size={32} /> : <Utensils size={32} />}</span><h3>{savedOnly && !saved.length ? t.savedEmpty : t.empty}</h3><p>{savedOnly && !saved.length ? t.savedEmptyBody : t.emptyDescription}</p>{savedOnly && !saved.length ? <Link to="/#discover" className="button button-primary">{t.explore}<ArrowRight size={17} /></Link> : <button className="button button-secondary" onClick={reset}>{t.reset}<X size={16} /></button>}</div> : view === 'map' ? <Suspense fallback={<div className="map-loading"><Map size={25} /><span>{lang === 'en' ? 'Unfolding Paris…' : 'Déplions Paris…'}</span></div>}><ParisMap places={results} lang={lang} t={t} onSelect={onSelect} /></Suspense> : <div className="place-grid">{visible.map(place => <PlaceCard key={place.id} place={place} t={t} lang={lang} saved={saved.includes(place.id)} onSave={() => onSave(place.id)} onSelect={() => onSelect(place)} />)}</div>}
    {results.length > 0 && <div className="directory-bottom"><p><ShieldCheck size={14} /><strong>{t.directory}</strong><span className="middle-dot">·</span><span>{t.directoryNote}</span></p>{results.length > 3 && view === 'list' && category === 'all' && !query && district === 'all' && price === 'all' && !savedOnly && <button className="text-link" onClick={() => setExpanded(!expanded)}>{expanded ? t.viewLess : t.viewAll}<ArrowDown size={15} className={expanded ? 'rotate-arrow' : ''} /></button>}</div>}
    <AnimatePresence>{filtersOpen && <Modal title={t.filters} onClose={() => setFiltersOpen(false)}><div className="modal-heading"><span className="modal-icon"><SlidersHorizontal size={24} /></span><h2>{t.filters}</h2><p>{t.subtitle}</p></div><div className="filter-form"><fieldset><legend>{t.price}</legend>{[{ value: 'all', text: t.anyPrice }, { value: '0', text: t.freeOnly }, { value: '1', text: t.euroOnly }].map(item => <label className={`radio-option ${price === item.value ? 'selected' : ''}`} key={item.value}><input type="radio" name="budget" value={item.value} checked={price === item.value} onChange={() => setPrice(item.value)} />{item.text}{price === item.value && <Check size={17} />}</label>)}</fieldset><label className="sort-label">{t.sort}<select value={sort} onChange={event => setSort(event.target.value)}><option value="recommended">{t.recommended}</option><option value="alphabetical">{t.alphabetical}</option></select></label><div className="filter-actions"><button className="text-link" onClick={reset}>{t.reset}</button><button className="button button-primary" onClick={() => setFiltersOpen(false)}>{t.apply} ({results.length})<ArrowRight size={17} /></button></div></div></Modal>}</AnimatePresence>
  </section>
}

function CommunityBanner({ t }: { t: Copy }) {
  return <section className="community-banner container"><div className="community-art" aria-hidden="true"><div className="mini-plate"><Smile size={58} strokeWidth={1} /></div><span className="heart-float">♥</span><span className="community-spark">✳</span></div><div><span className="eyebrow">{t.bottomEyebrow}</span><h2>{t.bottomTitle}</h2><p>{t.bottomBody}</p></div><Link to="/about" className="button button-secondary">{t.bottomCta}<ArrowUpRight size={18} /></Link></section>
}

function About({ t, lang }: { t: Copy; lang: Lang }) {
  return <main id="main" className="about-page container"><Link to="/" className="text-link back-link"><ArrowLeft size={16} />{t.back}</Link><div className="about-intro"><span className="eyebrow"><Heart size={15} /> BON APPÉTIT, EVERYONE.</span><h1>{t.aboutTitle}</h1><p>{t.aboutSubtitle}</p></div><div className="steps-grid">{[{ title: t.step1, body: t.step1Body, icon: Search }, { title: t.step2, body: t.step2Body, icon: ShieldCheck }, { title: t.step3, body: t.step3Body, icon: Utensils }].map((step, index) => <Tilt className="step-card" key={step.title}><div className="step-top"><step.icon size={27} strokeWidth={1.5} /><span>0{index + 1}</span></div><h2>{step.title}</h2><p>{step.body}</p></Tilt>)}</div><section className="source-section"><div><span className="eyebrow">SOURCES, NOT SPONSORED.</span><h2>{t.sources}</h2><p>{t.sourcesBody}</p><div className="source-links"><a href="https://www.crous-paris.fr/se-restaurer/nos-sites-de-restauration/" target="_blank" rel="noreferrer">CROUS Paris<ArrowUpRight size={17} /></a><a href="https://maison-etudiante.paris/en/distributions-alimentaires/" target="_blank" rel="noreferrer">Maison étudiante · Linkee<ArrowUpRight size={17} /></a><a href="https://cop1.fr/ville/paris/" target="_blank" rel="noreferrer">Cop1 Paris<ArrowUpRight size={17} /></a><a href="https://www.etudiant.gouv.fr/fr/comment-beneficier-du-repas-crous-1-eu-3123" target="_blank" rel="noreferrer">{lang === 'en' ? 'The €1 meal explained' : 'Le repas à 1 € expliqué'}<ArrowUpRight size={17} /></a></div></div><div className="data-note"><div className="data-note-label"><span />{lang === 'en' ? 'DIRECTORY MODE' : 'MODE ANNUAIRE'}</div><h3>{t.liveTitle}</h3><p>{t.liveBody}</p><div className="reviewed-date"><CheckCheck size={17} />{lang === 'en' ? 'Sources reviewed · 11 September 2026' : 'Sources consultées · 11 septembre 2026'}</div></div></section><CommunityBanner t={t} /></main>
}

function SignIn({ t, profile, onProfile }: { t: Copy; profile: string; onProfile: (name: string) => void }) {
  const [name, setName] = useState(profile)
  const navigate = useNavigate()
  function submit(event: FormEvent) { event.preventDefault(); if (!name.trim()) return; onProfile(name.trim()); navigate('/saved') }
  return <main id="main" className="signin-page container"><div className="signin-copy"><span className="eyebrow"><Utensils size={15} /> A SEAT AT THE TABLE.</span><h1>{profile ? `${t.welcome} ${profile}.` : t.signinTitle}</h1><p>{t.signinBody}</p><div className="signin-illustration" aria-hidden="true"><div className="signin-plate"><Smile size={86} strokeWidth={1} /></div><span>✦</span></div></div><div className="signin-form"><span className="modal-icon"><Bookmark size={26} /></span><h2>{t.localTitle}</h2><p>{t.localBody}</p><form onSubmit={submit}><label htmlFor="profile-name">{t.name}</label><input id="profile-name" placeholder={t.namePlaceholder} maxLength={40} autoComplete="given-name" value={name} onChange={event => setName(event.target.value)} required /><button className="button button-primary" type="submit">{t.continue}<ArrowRight size={18} /></button></form>{profile && <button className="text-link remove-profile" onClick={() => { onProfile(''); setName('') }}>{t.signout}<X size={15} /></button>}<div className="local-privacy"><ShieldCheck size={17} /><span>{t.noFees}</span></div></div></main>
}

function ScrollManager() {
  const { pathname, hash } = useLocation()
  useEffect(() => { if (hash) { const timer = setTimeout(() => document.querySelector(hash)?.scrollIntoView({ behavior: 'smooth' }), 80); return () => clearTimeout(timer) } else window.scrollTo(0, 0) }, [pathname, hash])
  return null
}

function Assiette() {
  const [theme, setTheme] = useStored<'light' | 'dark'>('assiette-theme', 'light')
  const [lang, setLang] = useStored<Lang>('assiette-lang', 'en')
  const [saved, setSaved] = useStored<string[]>('assiette-saved', [])
  const [profile, setProfile] = useStored('assiette-profile', '')
  const [selected, setSelected] = useState<Place | null>(null)
  const [privacyOpen, setPrivacyOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [toast, setToast] = useState('')
  const location = useLocation()
  const t = copy[lang]
  useEffect(() => { document.documentElement.dataset.theme = theme; document.documentElement.style.colorScheme = theme }, [theme])
  useEffect(() => { document.documentElement.lang = lang }, [lang])
  useEffect(() => { const frame = requestAnimationFrame(() => setMenuOpen(false)); return () => cancelAnimationFrame(frame) }, [location.pathname])
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 3200); return () => clearTimeout(timer) }, [toast])
  const savePlace = useCallback((id: string) => { const alreadySaved = saved.includes(id); setSaved(current => alreadySaved ? current.filter(item => item !== id) : [...current, id]); setToast(alreadySaved ? t.removedToast : t.savedToast) }, [saved, setSaved, t])
  return <>
    <ScrollManager /><a className="skip-link" href="#main">{lang === 'en' ? 'Skip to content' : 'Aller au contenu'}</a>
    <header className="site-header"><div className="header-inner"><Brand /><nav className="desktop-nav" aria-label="Main navigation"><NavLink to="/" end>{t.find}</NavLink><NavLink to="/about">{t.about}</NavLink><NavLink to="/saved">{t.saved}{saved.length > 0 && <span className="saved-count">{saved.length}</span>}</NavLink></nav><div className="header-actions"><span className="paris-chip"><span />Paris, France</span><span className="header-divider" /><button className="language-button" onClick={() => setLang(lang === 'en' ? 'fr' : 'en')} aria-label={lang === 'en' ? 'Switch to French' : 'Passer en anglais'}><span className={lang === 'en' ? 'active' : ''}>EN</span><span className="language-slash">/</span><span className={lang === 'fr' ? 'active' : ''}>FR</span></button><button className="theme-button icon-button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}>{theme === 'light' ? <Moon size={18} /> : <Sun size={19} />}</button><Link to="/signin" className="signin-link">{profile || t.signIn}<ArrowUpRight size={15} /></Link><button className="mobile-menu icon-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation" aria-expanded={menuOpen}>{menuOpen ? <X size={22} /> : <Menu size={22} />}</button></div></div>{menuOpen && <nav className="mobile-nav" aria-label="Mobile navigation"><NavLink to="/" end>{t.find}<ArrowUpRight size={16} /></NavLink><NavLink to="/about">{t.about}<ArrowUpRight size={16} /></NavLink><NavLink to="/saved">{t.saved} ({saved.length})<Bookmark size={16} /></NavLink><NavLink to="/signin">{profile || t.signIn}<ArrowUpRight size={16} /></NavLink></nav>}</header>
    <Routes><Route path="/" element={<main id="main"><Hero t={t} /><TrustStrip t={t} /><Directory t={t} lang={lang} saved={saved} onSave={savePlace} onSelect={setSelected} /><CommunityBanner t={t} /></main>} /><Route path="/about" element={<About t={t} lang={lang} />} /><Route path="/saved" element={<main id="main" className="saved-page"><Directory t={t} lang={lang} saved={saved} onSave={savePlace} onSelect={setSelected} savedOnly /><CommunityBanner t={t} /></main>} /><Route path="/signin" element={<SignIn t={t} profile={profile} onProfile={setProfile} />} /><Route path="*" element={<main id="main" className="empty-state not-found"><span className="eyebrow">404 · OFF THE MENU</span><h1>{lang === 'en' ? 'This plate is empty.' : 'Cette assiette est vide.'}</h1><Link to="/" className="button button-primary">{t.back}<ArrowRight size={17} /></Link></main>} /></Routes>
    <footer className="site-footer container"><div className="footer-top"><div><Brand small /><p>{t.footer}</p></div><div className="footer-links"><Link to="/about">{t.about}</Link><button onClick={() => setPrivacyOpen(true)}>{t.privacy}</button><span className="footer-made">Paris, with <Heart size={13} /></span></div></div><div className="footer-bottom"><span>© 2026 Assiette</span><p>{t.disclaimer}</p><span className="footer-bon">Bon appétit <Utensils size={12} /></span></div></footer>
    <AnimatePresence>{selected && <Modal title={selected.name} onClose={() => setSelected(null)} wide><div className="detail-photo"><img src={selected.image} alt={selected.imageAlt} /><span className="detail-price">{selected.price ? '1€' : t.free}</span></div><div className="detail-content"><span className="eyebrow">{selected.category === 'crous' ? t.mealTag : t.basketTag}</span><h2>{selected.name}</h2><p className="detail-area"><MapPin size={15} />{lang === 'en' ? selected.area : selected.areaFr}</p><p>{lang === 'en' ? selected.description : selected.descriptionFr}</p><div className="eligibility-note"><CircleHelp size={21} /><div><h3>{t.eligibility}</h3><p>{selected.category === 'crous' ? t.restaurantAdvice : t.basketAdvice}</p></div></div><div className="detail-source"><ShieldCheck size={15} /><span>{t.source}: <strong>{selected.sourceName}</strong></span><span>11.09.2026</span></div><div className="detail-actions"><a href={selected.source} target="_blank" rel="noreferrer" className="button button-primary">{t.officialPage}<ExternalLink size={16} /></a><button className={`button button-secondary ${saved.includes(selected.id) ? 'saved-action' : ''}`} onClick={() => savePlace(selected.id)}><Bookmark size={17} fill={saved.includes(selected.id) ? 'currentColor' : 'none'} />{saved.includes(selected.id) ? t.unsave : t.save}</button></div>{selected.coordinates && <a className="text-link directions-link" href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selected.name + ' Paris')}`} target="_blank" rel="noreferrer"><MapPin size={15} />{t.directions}<ArrowUpRight size={15} /></a>}<p className="photo-note">{t.photoNote}</p></div></Modal>}{privacyOpen && <Modal title={t.privacyTitle} onClose={() => setPrivacyOpen(false)}><div className="privacy-modal"><span className="modal-icon"><ShieldCheck size={26} /></span><h2>{t.privacyTitle}</h2><p>{t.privacyBody}</p><button className="button button-secondary" onClick={() => { setSaved([]); setToast(t.dataCleared); setPrivacyOpen(false) }}>{t.clearData}<X size={16} /></button></div></Modal>}</AnimatePresence>
    <AnimatePresence>{toast && <motion.div className="toast" role="status" initial={{ opacity: 0, y: 30, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 20 }}><span><Check size={16} /></span>{toast}<button onClick={() => setToast('')} aria-label={t.close}><X size={15} /></button></motion.div>}</AnimatePresence>
  </>
}

export default function App() { return <BrowserRouter><Assiette /></BrowserRouter> }
