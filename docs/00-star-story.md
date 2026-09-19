# The Assiette Story — told the STAR way

**What this document is:** the whole Track 3 project, from "why" to "so what," written the way you'd explain it to a friend, a recruiter, or Mr. Weng Wei — not the way you'd write it for a computer science exam. It uses the **STAR method** (Situation → Task → Action → Result), the same structure people use to tell a good story in a job interview. If you only read one document before presenting this project out loud, read this one.

Every technical fact in here (prices, API names, hours) matches the detailed docs. This file just tells the story in plain words first, with the detail available right underneath if someone wants to go deeper.

---

## The 30-second version

> Students in Paris are hungry and broke on a Tuesday evening, and there is no single place that tells them: *"here is a real meal you can afford, here is exactly how to get it, and here is what to say in French when you arrive."* I built **Assiette**, an AI assistant that answers that one question honestly, using real government meal data and a hand-checked list of free food programs — and it refuses to make anything up.

Everything below is that sentence, unpacked.

---

## S — Situation: what was actually going on

Picture a normal Tuesday. It's 18:20. Classes just ended. You have €3 left for the day, you're in the 13th arrondissement, and you are hungry. What do you actually do?

**Option 1 — You check the CROUS app.** CROUS is the French national body that runs subsidized student restaurants. Their menus are there, but the app just lists restaurants — it doesn't know your budget, your location, or that it's already 18:20 and half the restaurants closed after lunch. It's like a shop directory with no idea which shops are open right now or whether you can afford anything inside.

**Option 2 — You try to remember which charity is giving out food tonight.** Groups like *Linkee*, *Cop1*, and *Restos du Cœur* run free food distributions for students — but each one has its own website, its own hours, and its own rules about who qualifies and whether you need to register in advance. One is Monday only. Another needs an account made two days ago. A third requires an in-person interview before they'll even give you anything. None of this is written down in one place.

**Option 3 — You guess, and you're often wrong.** You walk to a restaurant that turns out to be lunch-only. You show up at a food distribution that already closed its registration. You end up buying an overpriced kebab because it was the only thing open — and you didn't have the French vocabulary ready when you got there anyway.

**This is not a rare, one-off problem.** It is a decision that repeats almost every single day, for a huge number of international and budget-limited students in Paris — including me, right now, as an ESSEC–CentraleSupélec DSBA student. I have personally lost an evening to exactly this: bouncing between three tabs, not sure if a place was open, not knowing the right thing to say at the door.

**The gap wasn't "there's no data."** CROUS publishes real menus. Charities publish real schedules. The gap was that **nobody had put it together** — one tool that takes a normal sentence like *"I'm in the 13th, I have €3, and I need dinner after 6pm,"* and gives back one honest, specific answer.

*(Full version: [Phase 1 — Problem Statement](phase1-problem-statement.md))*

---

## T — Task: what I set out to do

Given that situation, the task I set myself — inside **Track 3: Building an AI-Powered Application** — was:

> Design and build the simplest possible AI application that turns a plain-language need ("cheap food, tonight, near me") into a trustworthy, specific answer — without ever inventing information.

That last part — **without ever inventing information** — turned out to be the entire design challenge. It would have been easy to build a chatbot that sounds confident about Paris food options. It is much harder to build one that is only *allowed* to talk about places that are actually real, actually open, and actually verified — and that says "I don't know" instead of guessing when the data runs out.

So the real task had three parts:

1. **Understand the person, not the technology first.** Who exactly is hungry, when, and why do today's options fail them? (This became [Phase 1](phase1-problem-statement.md).)
2. **Design the smallest honest version of a solution** — what data it needs, what the AI is and isn't allowed to do, and what to deliberately leave out of version 1. (This became [Phase 2](phase2-solution-spec.md).)
3. **Get a second opinion before writing code**, from someone with 20+ years building AI products, on exactly where this idea could quietly fail. (This became [Phase 3](phase3-tutor-briefing.md).)
4. **Actually build it, and then be honest about what building it taught me** that reading and planning never could. (This became [Phase 4](phase4-reflection.md) and the working app.)

---

## A — Action: what I actually did, step by step

Think of this like a recipe with four steps. Each step produced a real document or a real piece of software — nothing here is theoretical.

### Action 1 — I wrote down the problem like a human, not a spec

Before touching any code or any AI tool, I wrote a plain problem statement: **who** is affected (international/budget-limited students in Paris), **how often** (almost daily, concentrated 17:30–20:30), **what they try today** (four incomplete options — official menus, scattered charity pages, maps/social media, or just guessing) and **why each one fails**, and **why I'm the person who should build this** (I live the problem, I can test it with real classmates, and I have the data skills to build the "smart matching" part instead of just another list).

*Where to find it: [Phase 1 — Problem Statement](phase1-problem-statement.md).*

### Action 2 — I designed the smallest honest version of the app

I decided, on paper first, exactly what the AI is for and — just as importantly — exactly what it is **not** for.

**What the AI actually does**, explained without jargon:

- **It reads.** It looks at a real, live government feed of Paris student restaurant menus (from an official CROUS data source), plus a hand-checked list of about 15 food-charity locations I researched and verified myself (Linkee, Cop1, Restos du Cœur, Secours Populaire, and others), plus a small notes file about eligibility rules and useful French phrases.
- **It sorts.** Given your area, your budget, and the time, it ranks the real options — closest first, cheapest first, actually-open-right-now first. This part is just arithmetic and logic; no AI "creativity" involved, on purpose.
- **It explains, but only using what it found.** Only at the very last step does a language model write a short, friendly summary and the French phrases you'd need — and it is only allowed to talk about the specific places that were already found and verified in the step before. If the sorting step found nothing good, the AI's job is to say so honestly, not to invent a restaurant.

I designed two moments that matter most to a real user: (A) *ask once, get a short shortlist*, and (B) *open one option, and leave the app ready to actually walk in the door and speak French*. I explicitly wrote down what I would **not** build in version 1 — no live booking of food-charity slots (that requires their own logins), no voice, no accounts, no cities outside Paris, no languages beyond English and French. Saying "not yet" clearly is what kept the project shippable in days instead of months.

I also hand-drew three screens (home screen, results screen, detail screen) before writing any interface code, so the shape of the experience was decided by the problem, not by whatever a coding tool defaulted to.

*Where to find it: [Phase 2 — Solution Spec](phase2-solution-spec.md) and [the three wireframes](wireframes/index.html).*

### Action 3 — I got pressure-tested before building, not after

Rather than build first and hope, I compressed Phases 1 and 2 into a single one-page brief and booked a 30-minute conversation with Mr. Weng Wei, an AI Super-Individual with 20+ years of engineering and startup experience. I prepared three specific, non-generic questions instead of vague ones:

1. Given that my data sources are a mix of one clean government API and several messy charity websites, is my plan technically solid — or is "confidently making things up" the failure mode I should be designing against hardest?
2. What actually goes wrong with apps like this in the real world (stale information, students trusting a fluent sentence over an actual timestamp, and so on) — and how do I defend a live demo against that?
3. If he had my exact plan and no funding, what would he personally build *first*, this weekend — the simple filtering logic, or the language-model part?

*Where to find it: [Phase 3 — Tutor Briefing](phase3-tutor-briefing.md) and the [one-pager](phase3-one-pager.md).*

### Action 4 — I built the real thing, honestly, and then wrote down what it taught me

I built a working prototype (Python + Streamlit, a simple way to turn Python code into a usable web app) that does exactly what I promised in Phase 2 — nothing more, nothing invented:

- A small piece of code that talks to the real CROUS data feed and remembers ("caches") the answer for half an hour so it doesn't hammer the government's server.
- A hand-built, source-cited list of Paris food-charity locations, each one tagged with the date I personally verified it.
- A scoring system that ranks all the options by distance, price, and whether they're actually open at the time you asked — plain logic, no AI involved yet.
- A language model (`openai/gpt-oss-20b`, running through a free service called Groq) that writes the final friendly summary and French phrases — but the code actively **deletes** any suggestion the model makes if it mentions a place that wasn't in the verified list. The rule isn't just a polite request in a prompt; it's enforced in the code afterward.
- A fallback path: if the internet, the government API, or the AI service is down, the app still works using a saved snapshot and a template answer instead of crashing or going silent.
- Automated tests that check the logic actually behaves the way I claimed it would (for example: does a €3 budget correctly rule out a €3.30 meal and correctly surface a free option instead?).

Then — separately from the code — I wrote an honest two-page reflection on what surprised me, what I'd change, and whether this could realistically become a business (short answer: not on top of this particular free data feed, because its terms explicitly forbid commercial use — but it could realistically live on as a non-profit or campus tool).

*Where to find it: the working app (`frontend/` + `backend/api.py` and the `assiette/` code), and [Phase 4 — Reflection](phase4-reflection.md).*

---

## R — Result: what came out of it, and why it matters

**A concrete, working thing exists**, not just a slide deck: type a sentence like *"I'm in the 13th, €3 budget, dinner after 18:00,"* and the app returns a short, ranked list of real places, tells you honestly whether each one is actually open right now, shows the real menu or the real eligibility rule, and gives you the French sentence to say at the door — with the date each fact was checked, visible on screen.

**It behaves safely on purpose.** If the AI part of the system ever tried to suggest somewhere that wasn't actually found and verified, the code throws that suggestion away before the user ever sees it. That single design decision is the most important result of the whole project: it proves, in working software, that "an AI feature" and "a trustworthy AI feature" are not the same thing — and that the second one takes deliberate engineering, not just a good prompt.

**It's honest about its own limits, in writing.** The reflection names the real weak point (charity opening hours change, and this version can't see live booking slots) instead of hiding it, and it gives a real, specific answer to "could this be a business" — including the inconvenient fact that the free government data feed I used legally cannot be used commercially. That is the kind of finding you can only get by actually building something and hitting the wall, not by planning forever.

**It is reusable, beyond this course.** The three documents that other students, a hiring manager, or Mr. Weng Wei might actually read — the problem statement, the spec, and the reflection — are written in plain language on purpose, so the project can be explained out loud in under two minutes without losing what makes it credible.

---

## Say it back in one breath (the STAR summary)

- **Situation:** Paris students face a daily, unsolved, unglamorous problem — where to get an affordable meal tonight — because the real answer is scattered across a government menu app and a dozen uncoordinated charity websites.
- **Task:** Design and build the smallest AI application that answers this honestly, using real data, without ever inventing an answer.
- **Action:** I wrote the problem down like a human first, designed exactly what the AI would and would not do, pressure-tested the plan with an experienced engineer before writing code, then built and tested a working prototype that enforces its own honesty in code, not just in a prompt.
- **Result:** A working, tested app that gives real students a real, timestamped, source-backed answer — plus a written reflection that is upfront about what would need to change for this to become more than a course project.

---

## A note on how to read the rest of the folder

If you only have five minutes: read this document, then skim the [Phase 4 reflection](phase4-reflection.md) for the "so what."

If you have thirty minutes (or you're Mr. Weng Wei): read [Phase 1](phase1-problem-statement.md) → [Phase 2](phase2-solution-spec.md) → [the wireframes](wireframes/index.html) → this document → [Phase 4](phase4-reflection.md).

If you want to actually try it: see the [README](../README.md) for how to run the app.
