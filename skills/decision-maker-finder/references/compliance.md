# What the law actually requires

B2B prospecting is lawful in every market covered here. The rules govern **how**
you obtain details and **what you may then do with them**, and they differ
enough that advice correct in Mumbai is unlawful in Toronto.

This is orientation for giving the user accurate guidance, not legal advice.
For a campaign at scale, or any processing of EU personal data, the user should
take actual counsel.

## Contents

- [The one rule everywhere](#the-one-rule-everywhere)
- [India: DPDP Act and TRAI](#india-dpdp-act-and-trai)
- [EU and UK: GDPR](#eu-and-uk-gdpr)
- [United States: CAN-SPAM and TCPA](#united-states-can-spam-and-tcpa)
- [Canada: CASL](#canada-casl)
- [Other markets](#other-markets)
- [Practical defaults](#practical-defaults)

---

## The one rule everywhere

**An opt-out is permanent and crosses channels.** Someone who says no to email
has not invited a call. Someone who unsubscribed in 2024 is still unsubscribed.
Every regime here enforces this, and it is also the only rule that is
straightforwardly right regardless of enforcement.

Keep a suppression list, honour it across every channel and every campaign, and
never route around it with a different sending domain. That last move is
treated as an aggravating factor by regulators, not a clever workaround.

## India: DPDP Act and TRAI

**Digital Personal Data Protection Act, 2023.** India's data protection regime
is consent-forward and applies to digital personal data.

- Personal data processed for a lawful purpose generally requires **consent**,
  which must be free, specific, informed and unambiguous, with a notice.
- The Act's carve-outs include **publicly available personal data** that the
  person concerned has themselves made public — the provision most relevant to
  professional-capacity B2B research.
- Data principals hold rights to access, correction and erasure, and the
  requirement to act on an erasure request is real.
- Rules and enforcement machinery have been phasing in; treat the direction as
  settled and the operational detail as something to check at the time.

**Practical reading:** identifying a professional's work role and work contact
from sources they or their employer made public sits comfortably within normal
B2B practice. Building a database of personal mobile numbers of unclear
provenance does not.

**TRAI — calls and SMS.** Separate from data protection and enforced far more
actively in practice:

- The **DND / DNC registry** governs unsolicited commercial communication to
  Indian telecom subscribers.
- Commercial senders must register under TRAI's framework, use registered
  headers and pre-approved templates for SMS, and scrub against preferences.
- Penalties fall on the sender and on the telecom resources used — losing a
  sending header is a genuine operational risk.
- A one-to-one call to a company switchboard about a specific proposal is not
  the same activity as a campaign. Volume and automation are what move you into
  the regulated category.

**WhatsApp** for business outreach in India runs under Meta's Business
Messaging policy in addition to TRAI: template approval, opt-in expectations,
and account bans for unsolicited messaging. It is not a way around SMS rules.

## EU and UK: GDPR

The strictest regime here, and the one most often waved away incorrectly.

- **B2B is not exempt.** A named person's work email at an identifiable
  employer is personal data. `firstname.lastname@company.com` is personal data;
  `info@company.com` generally is not.
- **Legitimate interest** (Art. 6(1)(f)) is the usual lawful basis for B2B
  prospecting, and it is available — but it is a *test*, not a label. It
  requires a documented balancing assessment (LIA) weighing your interest
  against the person's reasonable expectations.
- **Transparency.** Where data was not collected from the person, Art. 14
  requires telling them — who you are, what you hold, where you got it, and
  their rights — generally within a month or at first contact.
- **ePrivacy Directive** sits on top and governs electronic marketing. National
  implementations vary: several member states require **consent even for B2B
  email**. Ireland and the Netherlands distinguish corporate subscribers more
  permissively; Germany and Austria are the strict end.

**Germany is the case to get right, because GDPR is not the operative rule.**
Unsolicited advertising email is governed by **§ 7 Abs. 2 Nr. 2 UWG** (the
Act Against Unfair Competition), which requires **prior express consent** and
has **no B2B carve-out**. GDPR governs whether you may *process* the person's
data; UWG governs whether you may *send to the channel*. A documented
legitimate-interest assessment satisfies the first and does nothing for the
second — this is the distinction most prospecting advice gets wrong.

Note the asymmetry inside the same provision: **§ 7 Abs. 2 Nr. 1** allows B2B
*telephone* contact on presumed consent, so the switchboard is available where
email is not.

The practical risk is not the statutory fine. It is the **Abmahnung** — a
lawyer's cease-and-desist, a few hundred euros direct, attached to a
**Unterlassungserklärung** the recipient signs carrying a contractual penalty
for any repeat. That undertaking is permanent and expensive, and issuing them
is a routine business in Germany. Austria's § 107 TKG works similarly.
- **Rights to object and to erasure** must be honoured, and an objection to
  direct marketing is absolute — there is no balancing test to fall back on.
- **UK GDPR plus PECR** is materially similar; PECR is more permissive for
  corporate-subscriber email than several EU states.

**Practical reading:** for EU targets, tell the user plainly that a lawful basis
must be documented before the first email, that some member states require
consent outright, and that the source of the data has to be disclosed. This is
the market where "we bought a list" causes actual fines.

## United States: CAN-SPAM and TCPA

The most permissive major market for **email**, and among the harshest for
**phone**.

**CAN-SPAM** — no prior consent required for commercial email. Requirements are
about the message:

- Accurate header and routing information; no deceptive subject line
- Identify the message as an advertisement where it is one
- A valid physical postal address
- A working opt-out honoured within 10 business days, free and without
  requiring an account
- Liability extends to the company whose product is promoted, not only the
  sender

**TCPA and the National Do Not Call Registry** — cold *calling* is a different
matter:

- Autodialers, prerecorded messages and marketing texts to mobile numbers
  carry statutory damages per message, and this is heavily litigated
- Business-to-business calls have narrower exemptions than commonly assumed,
  and state law frequently adds requirements beyond federal
- **Never text a US mobile as cold outreach.** The risk-to-reward is
  indefensible

**State privacy laws** — CCPA/CPRA in California and its successors in other
states now cover B2B contact data, granting access and deletion rights to
individuals including in a professional capacity.

## Canada: CASL

The strictest anti-spam regime in this list, and the one most often overlooked
because the email address looks North American.

- **Consent required before sending** — express, or implied on narrow grounds
- **Implied consent** includes a *conspicuously published* business email
  address where the message relates to the recipient's role and no statement
  refuses such messages. This is the usual basis for legitimate B2B outreach
  and it is narrower than it sounds: published, relevant, and not refused
- Every message needs sender identification, contact details, and a working
  unsubscribe honoured within 10 business days
- Penalties run to millions per violation, with personal liability for
  directors and officers

**Practical reading:** for Canadian targets, the address must have been
published by the company, the message must genuinely relate to that person's
job, and the unsubscribe must work. Pattern-inferred addresses do not meet the
implied-consent test — the address has to have been *published*.

## Other markets

- **Australia — Spam Act.** Consent-based, with inferred consent for
  conspicuously published work addresses relevant to the role. Similar shape to
  CASL, applied less aggressively.
- **Singapore — PDPA.** Consent regime, with a **business contact information
  exclusion** that makes professional-capacity B2B outreach relatively
  straightforward. The DNC registry covers calls and texts.
- **UAE, Saudi Arabia.** Data protection laws are recent and evolving; check
  current requirements before any campaign.
- **Brazil — LGPD.** GDPR-shaped, including legitimate interest as a basis.

## Practical defaults

When advising the user, these hold up in every market above:

1. **Work identity, work channels.** Never personal email, home address or
   personal mobile.
2. **Say where you got their details** if asked, and be able to answer.
3. **Make the opt-out one click**, honour it immediately, apply it across
   channels, and never re-import a suppressed contact.
4. **Verify before sending.** Bounces damage domain reputation, and reputation
   damage is the cost that persists after the campaign ends.
5. **Volume changes the category.** One researched email to a named person
   about a real fit is prospecting. Ten thousand templated sends is a campaign,
   and campaigns attract the rules.
6. **For EU, UK and Canadian targets, flag the requirement explicitly** rather
   than letting the user assume US rules travel. They do not.
7. **When the user asks for something the regime forbids** — buying a mobile
   number list for TCPA-covered outreach, emailing German B2B contacts without
   consent — say so plainly and give them the compliant route to the same
   outcome. There usually is one, and it is usually the switchboard or a warm
   introduction.
