export type Lang = 'en' | 'fr'
export type Category = 'all' | 'crous' | 'distribution'
export type Place = {
  id: string
  name: string
  category: Exclude<Category, 'all'>
  area: string
  areaFr: string
  description: string
  descriptionFr: string
  district: string
  image: string
  imageAlt: string
  price: number
  source: string
  sourceName: string
  location: string
  coordinates?: [number, number]
}

export const places: Place[] = [
  {
    id: 'mabillon', name: 'CROUS Mabillon', category: 'crous',
    area: '6th arrondissement · Saint-Germain', areaFr: '6e arrondissement · Saint-Germain',
    description: 'A proper lunch, in the heart of the Left Bank.', descriptionFr: 'Un vrai déjeuner, au cœur de la rive gauche.',
    district: '6', image: '/images/meal-bowl.jpg', imageAlt: 'A colorful bowl of rice and vegetables; illustrative meal photo',
    price: 1, source: 'https://www.crous-paris.fr/se-restaurer/nos-sites-de-restauration/', sourceName: 'CROUS Paris',
    location: 'Mabillon, Paris 6e. Confirm the entrance on the official CROUS page.', coordinates: [48.8525, 2.3355],
  },
  {
    id: 'linkee', name: 'Linkee food baskets', category: 'distribution',
    area: 'Across Paris · Student distributions', areaFr: 'Partout à Paris · Distributions étudiantes',
    description: 'Good food rescued. A little more in your cupboard.', descriptionFr: 'Des aliments sauvés. Un placard un peu plus rempli.',
    district: 'all', image: '/images/vegetable-basket.jpg', imageAlt: 'An assortment of fresh vegetables; illustrative food basket photo',
    price: 0, source: 'https://maison-etudiante.paris/en/distributions-alimentaires/', sourceName: 'Maison étudiante · Linkee',
    location: 'Multiple distribution locations in Paris. Choose a location and time on the official registration page.',
  },
  {
    id: 'bullier', name: 'CROUS Bullier', category: 'crous',
    area: '5th arrondissement · Port-Royal', areaFr: '5e arrondissement · Port-Royal',
    description: 'Your between-lectures, better-than-a-sandwich stop.', descriptionFr: 'Votre pause entre deux cours, mieux qu’un sandwich.',
    district: '5', image: '/images/pasta.jpg', imageAlt: 'A plate of creamy pasta; illustrative meal photo',
    price: 1, source: 'https://www.crous-paris.fr/se-restaurer/nos-sites-de-restauration/', sourceName: 'CROUS Paris',
    location: '39 avenue Georges Bernanos, Paris 5e. Confirm access and hours with CROUS.', coordinates: [48.8393, 2.3366],
  },
  {
    id: 'cop1', name: 'Cop1 student baskets', category: 'distribution',
    area: 'Across Paris · Student solidarity', areaFr: 'Partout à Paris · Solidarité étudiante',
    description: 'A helping hand, a full basket. No judgment.', descriptionFr: 'Un coup de main, un panier plein. Sans jugement.',
    district: 'all', image: '/images/food-basket.jpg', imageAlt: 'A person holding a paper grocery bag; illustrative distribution photo',
    price: 0, source: 'https://cop1.fr/ville/paris/', sourceName: 'Cop1 Paris',
    location: 'Multiple locations in Paris. The address is provided when you select a distribution on Cop1.',
  },
]

export const copy = {
  en: {
    find: 'Find a meal', about: 'How it works', saved: 'Saved places', signIn: 'Sign in',
    location: 'PARIS, À TABLE.', heroLine1: 'Good food.', heroLine2: 'Small budget.',
    heroBody: 'Student life is full enough. Your plate should be, too.',
    heroBody2: 'Find affordable CROUS meals and free food distributions around Paris. Less searching, more eating.',
    explore: 'Find my next meal', how: 'How does it work?', students: 'Made for Paris students',
    noFees: 'No fees. No fuss. Just food.', from: 'A FULL MEAL FROM', studentPrice: 'The student-friendly kind.',
    plateLabel: 'a little more on your plate.', official: 'Straight from the source', officialSub: 'CROUS & trusted associations',
    budget: 'Kind to your budget', budgetSub: '€1 meals & free food baskets',
    community: 'For every kind of student', communitySub: 'Good food belongs to everyone',
    heading: 'What’s on the menu?', subtitle: 'A good meal is closer than you think.',
    all: 'All options', crous: 'CROUS meals', distribution: 'Food distributions',
    search: 'Search a place or neighborhood', allParis: 'All of Paris', filters: 'Filters',
    list: 'List', map: 'Map', options: 'places to explore', viewAll: 'Explore all places', viewLess: 'Show fewer places',
    free: 'Free', perMeal: '/ meal', details: 'Take a look', source: 'Official source',
    mealTag: 'CROUS RESTAURANT', basketTag: 'FOOD DISTRIBUTION',
    schedule: 'Check today’s menu', registration: 'Registration required',
    directory: 'Source-backed directory', directoryNote: 'Menus and schedules can change. Photos are illustrative.',
    empty: 'Nothing on this plate yet.', emptyDescription: 'Try another neighborhood or clear your filters to find your next meal.',
    reset: 'Clear filters', price: 'Your budget', anyPrice: 'Any budget', freeOnly: 'Free options', euroOnly: '€1 meals',
    apply: 'Show results', sort: 'Sort by', recommended: 'Recommended', alphabetical: 'Name, A–Z',
    save: 'Save place', unsave: 'Remove from saved', savedToast: 'Added to your saved places', removedToast: 'Removed from saved places',
    savedTitle: 'Your little black book.', savedSubtitle: 'Good places are worth keeping. Saved on this device, just for you.',
    savedEmpty: 'Your next favorite is out there.', savedEmptyBody: 'Tap the bookmark on any place to keep it here. No account needed.',
    back: 'Back to all places', bottomEyebrow: 'A LITTLE SOLIDARITY GOES A LONG WAY',
    bottomTitle: 'Full plates. Fuller student lives.', bottomBody: 'Because choosing between lunch and your next textbook shouldn’t be a thing.',
    bottomCta: 'Meet Assiette', footer: 'Made with care, for student life in Paris.',
    disclaimer: 'An independent, non-commercial guide. Not a booking service.',
    privacy: 'Privacy & your data', aboutTitle: 'A better-fed student life.', aboutSubtitle: 'A small guide with a simple belief: a good meal should be within everyone’s reach.',
    step1: 'Find your kind of food', step1Body: 'Browse CROUS restaurants and food distributions. Filter by neighborhood and budget, or explore the map.',
    step2: 'Get the full picture', step2Body: 'Check the place details and follow the official source for menus, opening hours, eligibility, and availability.',
    step3: 'Go fill your plate', step3Body: 'Head to your restaurant, or register directly with the association. Assiette never handles bookings or payments.',
    sources: 'Good information. No guesswork.', sourcesBody: 'We point you to CROUS and established student associations, not paid listings. Our source references were reviewed on 11 September 2026.',
    liveTitle: 'A directory, not a live menu', liveBody: 'No live menu API or automated refresh service is connected. We do not claim that a venue is open now, or that a particular dish or basket is available. Always check the official page before traveling.',
    eligibility: 'Before you go', officialPage: 'Visit the official source', directions: 'Get directions',
    restaurantAdvice: 'CROUS lists a €1 full meal for all students. Check today’s menu, opening hours, student identification, and accepted payment methods with CROUS.',
    basketAdvice: 'Distributions are free for students, but registration is required. Choose a date on the official page and bring proof of student status and a reusable bag. Contents and availability vary.',
    photoNote: 'Illustrative photo — not today’s menu or an exact basket.',
    privacyTitle: 'A little data. A lot of respect.', privacyBody: 'Assiette does not require an account. Your theme, language, and saved places stay in your browser’s local storage. We do not sell your data or collect payment information. The map loads tiles from OpenStreetMap, and external source links have their own privacy policies.',
    clearData: 'Clear my saved data', dataCleared: 'Your saved places have been cleared.', close: 'Close',
    signinTitle: 'Your next good meal starts here.', signinBody: 'Keep your favorite places close. Assiette works without a password, a subscription, or a complicated sign-up.',
    localTitle: 'Your own little corner', localBody: 'Create a profile on this device. Your name and saved places stay in this browser — there’s no online account or cross-device sync.',
    name: 'What should we call you?', namePlaceholder: 'Your first name', continue: 'Create my local profile', welcome: 'Welcome to the table,', signout: 'Remove local profile',
    mapNote: 'Approximate restaurant locations. Distribution addresses vary — check the official source.',
  },
  fr: {
    find: 'Trouver un repas', about: 'Comment ça marche', saved: 'Mes adresses', signIn: 'Se connecter',
    location: 'PARIS, À TABLE.', heroLine1: 'Bien manger.', heroLine2: 'Petit budget.',
    heroBody: 'La vie étudiante est déjà bien remplie. Votre assiette devrait l’être aussi.',
    heroBody2: 'Trouvez des repas CROUS abordables et des distributions gratuites à Paris. Moins chercher, mieux manger.',
    explore: 'Trouver mon prochain repas', how: 'Comment ça marche ?', students: 'Pensé pour les étudiants parisiens',
    noFees: 'Sans frais. Sans stress. À table.', from: 'UN REPAS COMPLET DÈS', studentPrice: 'Le bon plan étudiant.',
    plateLabel: 'un peu plus dans l’assiette.', official: 'Directement à la source', officialSub: 'CROUS et associations de confiance',
    budget: 'Doux pour le budget', budgetSub: 'Repas à 1 € et paniers gratuits',
    community: 'Pour tous les étudiants', communitySub: 'Bien manger, c’est pour tout le monde',
    heading: 'Quoi au menu ?', subtitle: 'Un bon repas n’est jamais bien loin.',
    all: 'Toutes les options', crous: 'Repas CROUS', distribution: 'Distributions',
    search: 'Rechercher un lieu ou un quartier', allParis: 'Tout Paris', filters: 'Filtres',
    list: 'Liste', map: 'Carte', options: 'adresses à découvrir', viewAll: 'Voir toutes les adresses', viewLess: 'Voir moins',
    free: 'Gratuit', perMeal: '/ repas', details: 'Découvrir', source: 'Source officielle',
    mealTag: 'RESTAURANT CROUS', basketTag: 'DISTRIBUTION ALIMENTAIRE',
    schedule: 'Voir le menu du jour', registration: 'Inscription nécessaire',
    directory: 'Des sources de confiance', directoryNote: 'Menus et horaires peuvent changer. Photos d’illustration.',
    empty: 'Cette assiette est encore vide.', emptyDescription: 'Essayez un autre quartier ou effacez les filtres pour trouver votre prochain repas.',
    reset: 'Effacer les filtres', price: 'Votre budget', anyPrice: 'Tous les budgets', freeOnly: 'Options gratuites', euroOnly: 'Repas à 1 €',
    apply: 'Voir les résultats', sort: 'Trier par', recommended: 'Recommandés', alphabetical: 'Nom, A–Z',
    save: 'Enregistrer', unsave: 'Retirer des favoris', savedToast: 'Ajouté à vos adresses', removedToast: 'Retiré de vos adresses',
    savedTitle: 'Votre petit carnet d’adresses.', savedSubtitle: 'Les bonnes adresses, ça se garde. Sur cet appareil, rien que pour vous.',
    savedEmpty: 'Votre prochaine pépite vous attend.', savedEmptyBody: 'Touchez le marque-page d’une adresse pour la garder ici. Sans compte.',
    back: 'Retour aux adresses', bottomEyebrow: 'UN PEU DE SOLIDARITÉ, ÇA CHANGE TOUT',
    bottomTitle: 'Des assiettes pleines. Des vies plus riches.', bottomBody: 'Parce qu’on ne devrait pas choisir entre déjeuner et son prochain manuel.',
    bottomCta: 'Découvrir Assiette', footer: 'Créé avec soin pour la vie étudiante à Paris.',
    disclaimer: 'Un guide indépendant et non commercial. Pas un service de réservation.',
    privacy: 'Vos données', aboutTitle: 'La vie étudiante, mieux nourrie.', aboutSubtitle: 'Un petit guide et une conviction simple : un bon repas devrait être à la portée de tous.',
    step1: 'Trouvez votre bonheur', step1Body: 'Explorez les restaurants CROUS et les distributions. Filtrez par quartier et budget ou parcourez la carte.',
    step2: 'Vérifiez les détails', step2Body: 'Consultez les informations et la source officielle pour les menus, horaires, conditions et disponibilités.',
    step3: 'Allez remplir votre assiette', step3Body: 'Rendez-vous au restaurant ou inscrivez-vous auprès de l’association. Assiette ne gère ni réservation ni paiement.',
    sources: 'De bonnes infos. Pas de suppositions.', sourcesBody: 'Nous vous guidons vers le CROUS et des associations reconnues, pas des annonces payantes. Sources consultées le 11 septembre 2026.',
    liveTitle: 'Un annuaire, pas un menu en direct', liveBody: 'Aucune API de menus ni actualisation automatique n’est connectée. Nous ne garantissons ni l’ouverture d’un lieu ni la disponibilité d’un plat ou panier. Vérifiez toujours la page officielle avant de partir.',
    eligibility: 'Avant de partir', officialPage: 'Consulter la source officielle', directions: 'Itinéraire',
    restaurantAdvice: 'Le CROUS propose un repas complet à 1 € pour tous les étudiants. Vérifiez le menu, les horaires, les justificatifs et les moyens de paiement auprès du CROUS.',
    basketAdvice: 'Les distributions sont gratuites pour les étudiants, sur inscription. Choisissez une date sur la page officielle, apportez un justificatif de scolarité et un sac. Le contenu et les disponibilités varient.',
    photoNote: 'Photo d’illustration — ne représente pas le menu du jour ou le panier exact.',
    privacyTitle: 'Peu de données. Beaucoup de respect.', privacyBody: 'Assiette ne nécessite pas de compte. Votre thème, langue et adresses restent dans le stockage local de votre navigateur. Nous ne vendons pas vos données. La carte utilise les tuiles OpenStreetMap. Les sites externes appliquent leur propre politique de confidentialité.',
    clearData: 'Effacer mes adresses', dataCleared: 'Vos adresses enregistrées ont été effacées.', close: 'Fermer',
    signinTitle: 'Votre prochain bon repas commence ici.', signinBody: 'Gardez vos bonnes adresses à portée de main. Sans mot de passe, abonnement ou inscription compliquée.',
    localTitle: 'Votre petit coin à vous', localBody: 'Créez un profil sur cet appareil. Votre nom et vos adresses restent dans ce navigateur : aucun compte en ligne ni synchronisation.',
    name: 'Comment vous appeler ?', namePlaceholder: 'Votre prénom', continue: 'Créer mon profil local', welcome: 'Bienvenue à table,', signout: 'Supprimer mon profil local',
    mapNote: 'Emplacements approximatifs. Les adresses de distribution varient : consultez la source officielle.',
  },
}

export type Copy = typeof copy.en
