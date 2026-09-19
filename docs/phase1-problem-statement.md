# Phase 1 — Problem Statement

**Project:** Assiette — Paris Student Meal Assistant
**Track:** 3 — Building an AI-Powered Application
**Author:** Trishit, ESSEC–CentraleSupélec DSBA M2
**Date:** September 2026
**STAR stage:** this document is the **Situation** (what's going on) and the start of the **Task** (what needs solving).

> **Read this in 20 seconds:** Students in Paris need cheap food almost every evening. The information to find it exists — but it's scattered across a government app and a dozen uncoordinated charity websites, in French, with no single place that says "here's what's open, near you, that you can afford, right now." That gap is the problem this project solves.

---

## A quick two-minute picture: meet Aïsha

Aïsha is a fictional but entirely typical composite of students around me — including me. It's Thursday, 18:10. She just left a group project meeting. She has €2.80 left for the day. She is in the 13th arrondissement (Paris is split into 20 numbered districts, like postcodes — this matters a lot for "can I actually walk there before it closes").

Here is what she actually has to do, today, with the tools that exist:

1. **Open the CROUS app** (CROUS is the French national agency that runs subsidised student restaurants; a full meal there is officially priced at **€3.30**, or **€1.00** if she receives a state grant). The app shows her a list of restaurants. It does not tell her which ones are still serving dinner at 18:10 — many university restaurants in Paris only serve lunch — and it does not know her budget is €2.80, which is 50 cents short of even the subsidised price.
2. **Try to remember which charity is active tonight.** She half-remembers that an organisation called *Linkee* gives out free food baskets, but she isn't sure which day, which location, or whether she needs to have registered online beforehand. She doesn't remember if she needs her student card, a bag, or both.
3. **Check Instagram and a WhatsApp group chat** for anything more current. Someone posted about a food distribution two weeks ago. It's not clear if it's still running, or if the post is stale.
4. **Give up and just walk somewhere.** She ends up at a restaurant that turns out to already be closed for the evening, and settles for a €9 sandwich — more than three times her remaining budget for the day.

Nothing in that story is exotic. It is the ordinary Tuesday-or-Thursday experience of a large number of international and budget-constrained students living in Paris, repeated **almost every single weekday**. This project starts here — with Aïsha's evening — not with a clever piece of technology looking for a use case.

---

## Who experiences this problem, and how often

International and budget-constrained students in Paris — including students newly arrived for a Grande École or university master's — face a daily question that is more logistical than culinary: *what can I eat tonight that I can afford, that I can reach after class, and that I am actually allowed to access?*

The decision happens almost every weekday evening, and again at lunch. It is not a once-a-semester administrative task. Hunger, a closing metro, a €3 remaining daily food budget, and a French form behind a login wall all collide between 17:30 and 20:30. For bursary students, CROUS meals at the social tariff are the backbone of the week. For others, a €3.30 CROUS tray is still the cheapest complete meal in the city — if they can find an open restaurant nearby whose menu they understand. For students in real precarity, the only viable option some evenings is a free food basket from Linkee, Cop1, Restos du Cœur, or Secours Populaire — if they know the site exists, if they registered in time, and if they can get there with a bag and a student card.

I live this as an international DSBA M2 student. So do the students around me: classmates comparing CROUS screenshots in group chats, people missing a Linkee slot because the information lived on Instagram, people paying €12 for a kebab because they could not decode whether the nearby RU (*restaurant universitaire* — the French short name for a CROUS restaurant) was still open.

## What they currently do, and why it is inadequate

Students currently stitch together four incomplete tools. None of them is "wrong" — each one is just built for a different, narrower job than the one a hungry student actually has.

| # | What students try | What it's actually good for | Why it still fails them |
|---|---|---|---|
| 1 | The official CROUS / CROUStillant menu app | Checking what's on the menu today at one specific restaurant | Doesn't know your budget, your arrondissement, or the time. Restaurant-first, not need-first. French-only labels confuse many international students, who often don't realise a "cafétéria" can still serve a subsidised meal |
| 2 | Charity/association websites (Linkee, Cop1, Restos du Cœur, Secours Populaire, Ordre de Malte…) | Publishing that week's real schedule for one specific organisation | Every charity has its own site, its own hours (which differ by weekday), and its own eligibility rule (some are "show your student card," others require a resource ceiling, proof of Paris housing, or a prior interview). Nothing combines them into "what's actually open for me, tonight" |
| 3 | Google Maps / Instagram / WhatsApp groups | Finding a restaurant that physically exists | Doesn't know student tariffs, doesn't know free-food eligibility, and social posts go stale within days |
| 4 | Walking somewhere and hoping | Nothing, really | The cost of being wrong is real: a closed restaurant, a distribution that already needed pre-registration, a volunteer asking for documents you didn't bring, and no French sentence ready when you arrive |

**In plain terms: the gap is not "there is no food data."** CROUS publishes real menus. Charities publish real schedules. **The gap is that nobody has unified it, filtered it to one person's real situation, and explained it back in a sentence that person can act on immediately** — in English or French. No current tool takes a sentence like *"it's Thursday, 18:10, I'm in the 13th, and I have €2.80"* and returns one grounded, ranked, same-evening answer that mixes paid subsidised meals and free distributions, with the French phrases needed at the door.

## Why I am the right person to address it

I am on both sides of the problem. I eat on a student budget in Paris, I have personally failed the current patchwork of tools (the same evening described above happened to me, not just to a fictional "Aïsha"), and I can test the result with a real community of international M2 classmates who will tell me immediately, bluntly, if a recommendation is wrong. As a DSBA student — someone trained to work with data and systems, not just prompts — I can treat this as a data problem first: live CROUS menus via a public API, a curated table of distribution points from the Maison étudiante and association pages, structured filters (place, budget, time, diet), then an AI model that is only allowed to speak about what that structured search actually found.

I am not starting from a model looking for a problem to solve. I am starting from real people who are hungry at 18:00 in a city whose cheapest food system is fragmented across a dozen French public and non-profit websites that don't talk to each other.

## Problem statement (one sentence)

**International and low-budget students in Paris must decide, almost daily, where to eat a complete meal they can afford and access that evening — and no existing tool combines live CROUS menus, student food-distribution rules, proximity, and language support into one grounded answer.**

---

## From Situation to Task, in one line

Given that situation, the task this project takes on — spelled out in full in [Phase 2](phase2-solution-spec.md) — is to design and build the **smallest possible AI application** that can answer Aïsha's question honestly: a real place, a real price, a real time window, and the French words to use when she gets there — without ever making anything up.

*Quick glossary, for anyone reading this who isn't a Paris student: **CROUS** is the French national student-services agency; it runs the subsidised restaurants. **Arrondissement** is one of Paris's 20 numbered districts. **RU** (*restaurant universitaire*) is French shorthand for a CROUS restaurant.*
