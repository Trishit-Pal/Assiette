# Assiette knowledge base

Last reviewed: 2026-09-14.
Use only as supporting context. Never invent a venue from this file. Venues must come from retrieved CROUS or distribution rows.

## CROUS prices and access

The official CROUS Paris page (updated 3 September 2026) publishes a **€1 complete meal for all students**, Monday–Friday, 11:30–14:30, one meal per service (restaurant, cafeteria, or self-service). Cafeterias also offer drinks and snacks through the weekday. Confirm student identification and payment on site or in Crous Mobile. Evening and weekend opening is site-specific; CROUS currently highlights Cité Internationale (23 boulevard Jourdan, 75014), La Barge (Port de la Gare, Quai François Mauriac, 75013), Restaurant Mabillon (3 rue Mabillon, 75006), and the Mab’Café (12 rue Clément, 75006). Assiette must not promise an evening hot meal at a site whose `jours_ouvert.soir` flag is false. Source: https://www.crous-paris.fr/se-restaurer/nos-sites-de-restauration/

## CROUStillant data rules

Menus and opening flags come from the CROUStillant API (api.croustillant.menu), which aggregates official CROUS data several times a day. The API is free, requires a custom User-Agent, limits 200 requests per minute, and **forbids commercial use**. Dates on menus are DD-MM-YYYY. If a menu is missing, say the menu is unavailable — do not invent dishes.

## Linkee

Linkee food distributions in Paris are open to all students. Create a beneficiary account, book the chosen distribution, bring a student card or certificat de scolarité, and bring a bag. One parcel per student per distribution. Cancel if you cannot attend. Assiette cannot see remaining slots.

Hours checked 2026-09-14: Monday 19:30–21:00 at ESS’Pace (15 rue Jean Antoine de Baïf, 75013); Tuesday 19:00–20:00 at La Maison Bleue (24 avenue de la Porte de Montmartre, 75018) on linkee.co (Maison étudiante still lists 18:30–20:00); Thursday 18:30–20:00 at Smart Food (80 rue des Haies, 75020). Source: https://linkee.co/distribution-paris/ and https://maison-etudiante.paris/distributions-alimentaires/

French at the door:
- Bonjour, je viens chercher mon panier Linkee. Voici ma carte étudiante.
- J’ai bien réservé en ligne. Faut-il un QR code ?
- Merci, j’ai un sac.

## Cop1 Solidarités Étudiantes

Cop1 is student-to-student aid. A student card or certificat de scolarité is enough to register for a basket on cop1.fr (Paris page). New baskets are typically published on Sundays. Contents vary: produce, cans, dry goods, hygiene products. Assiette cannot book a basket.

Checked 2026-09-14: Cop1’s own Paris page currently shows holiday closure until rentrée, and lists 13 rue Santeuil (75005) plus 18 rue Antoine Bourdelle (75015) without hours. Maison étudiante still lists weekly slots at Césure, Bastille, and quai d’Austerlitz. Do not add Bourdelle as a ticket until Cop1 publishes a schedule. Always confirm on https://cop1.fr/ville/paris/ before travelling.

French at the door:
- Bonjour, je suis inscrit·e pour un panier Cop1. Voici ma carte étudiante.
- Est-ce que je peux choisir les produits, ou c’est un colis déjà préparé ?
- Merci beaucoup pour votre aide.

## Restos du Cœur (student / youth centres in Paris)

Access requires an on-site enrolment interview. Bring ID, proof of housing in Paris (75) when required, and documents on income and charges (grant, CAF, pay slip, rent). Once enrolled you can take food aid immediately. This is not a drop-in CROUS meal. Source: Maison étudiante / Restos du Cœur de Paris.

French at the door:
- Bonjour, je viens pour une première inscription à l’aide alimentaire étudiante.
- J’habite à Paris, voici ma pièce d’identité et mon justificatif de logement.
- Quels documents faut-il pour l’entretien ?

## Secours Populaire (student antennas)

Aids are for students who live or study in Paris, after an interview, often with a remaining-living-cost criterion (reste à vivre). Some sites need an appointment by email (etudiants@secourspopparis.org). Do not send a student to a permanence as if it were an open buffet.

Checked 2026-09-14 on Maison étudiante: Bayet (6 rue Albert Bayet, 75013) Tuesdays 12:00–16:00 and Fridays 11:00–14:00 by mail appointment; Jussieu (4 place Jussieu, 75005) Thursdays 11:00–14:00 at the student-life desk, Sorbonne Université; Francis de Croisset (2 rue Francis de Croisset, 75018) Tuesdays and Thursdays 11:00–14:00 walk-in, Sorbonne Université — distinct from Restos du Cœur at number 8 on the same street.

French at the door:
- Bonjour, je suis étudiant·e et je viens pour un premier entretien d’aide alimentaire.
- J’ai envoyé un mail à l’antenne. Est-ce le bon créneau ?
- Voici ma carte étudiante et un justificatif de domicile.

## Ordre de Malte food truck

A reserved meal parcel (hot dish, dairy or dessert, fruit) plus sometimes produce. Booking via their form is mandatory. Show a student card; live in Paris or an adjacent commune. Do not present this as a walk-up CROUS restaurant.

French at the door:
- Bonjour, j’ai réservé un panier repas. Voici ma carte étudiante.
- Y a-t-il encore une option végétarienne aujourd’hui ?

## How to ask for a CROUS meal

- Bonjour, le repas à tarif étudiant, s’il vous plaît.
- Je suis boursier / boursière, c’est le tarif à un euro ?
- Il reste un plat sans viande ?
- L’addition, s’il vous plaît. Je paie par carte.

## Honesty rules for the assistant

If the requested evening has no open CROUS restaurant in range, say so clearly and pivot to distributions that match the weekday. If a distribution requires prior booking, say that in the first sentence of the card. Never claim how many parcels remain. Never list a restaurant or association that is not in the retrieved context. Prefer a smaller true itinerary over a long invented one.
