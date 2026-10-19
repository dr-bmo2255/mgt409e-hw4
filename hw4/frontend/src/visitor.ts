// Part E: who's visiting? The chat asks on arrival; the answer is remembered in this browser and
// changes the site (decade themes for alumni, "Yale overload" for rivals) and what we show first.

export type VisitorType = 'student' | 'alum' | 'family' | 'friend' | 'rival'

export type Visitor = {
  type: VisitorType
  decade?: Decade // alumni
  dan?: string // Dan asset picked (college / school / family member) for students and family
  label?: string // what they picked, for display ("Berkeley College", "Dad")
  rival?: RivalKey
  rivalModeOff?: boolean // rival fan, but the chat has moved on: the site is back to its normal look
}

export const WELCOME_QUESTION = 'Are you a Current Student, Alumnus, Family, Friend or Rival?'

export const VISITOR_CHOICES: { type: VisitorType; label: string }[] = [
  { type: 'student', label: 'Current Student' },
  { type: 'alum', label: 'Alumnus' },
  { type: 'family', label: 'Family' },
  { type: 'friend', label: 'Friend' },
  { type: 'rival', label: 'Rival' },
]

export const DECADES = ['1920s', '1930s', '1940s', '1950s', '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'] as const
export type Decade = (typeof DECADES)[number]

// What the site becomes for each decade, and Dan's line about it.
export const ERA: Record<Decade, { style: string; line: string }> = {
  '1920s': { style: 'Art Deco', line: "The bee's knees! Dan's dressed for a Gatsby party, and Campus Customs has gone full Art Deco." },
  '1930s': { style: 'Streamline Moderne', line: "Tune in! It's the golden age of radio, and the shop's gone Streamline Moderne." },
  '1940s': { style: 'Swing-era poster', line: 'Swing time! Dan cut a rug at the big-band dance, and the shop looks like a 1940s poster.' },
  '1950s': { style: 'Atomic diner', line: "Daddy-o! Dan's at the soda fountain, and the shop's all chrome and turquoise." },
  '1960s': { style: 'Mod & flower power', line: "Groovy! Dan's gone mod, and the whole shop is flower power." },
  '1970s': { style: 'Disco', line: 'Can you dig it? Dan hit the disco floor, and the shop is brown, orange and mustard.' },
  '1980s': { style: 'Neon synthwave', line: "Totally radical! Dan's got his boombox, and the shop is glowing neon." },
  '1990s': { style: 'Nineties web', line: "As if! Dan's chilling in flannel, and the shop is straight out of the '90s web." },
  '2000s': { style: 'Y2K gloss', line: "That's hot! Dan's got his flip phone, and the shop is glossy Y2K." },
  '2010s': { style: 'Flat design', line: 'Totally on fleek! Dan took a selfie, and the shop went flat and filtered.' },
  '2020s': { style: 'Today', line: "Welcome back, recent grad! Dan's on a video call, and the shop is just as you left it." },
}

export const decadeDan = (d: Decade, small = false) => `/media/dan/dan_${d}${small ? '_sm' : ''}.webp`

export const RIVALS = [
  { key: 'harvard', label: 'Harvard', taunt: 'that school up in Cambridge' },
  { key: 'princeton', label: 'Princeton', taunt: 'those orange tigers' },
  { key: 'brown', label: 'Brown', taunt: 'the bears of Providence' },
  { key: 'columbia', label: 'Columbia', taunt: 'the lions of Morningside Heights' },
  { key: 'cornell', label: 'Cornell', taunt: 'the Big Red up in Ithaca' },
  { key: 'dartmouth', label: 'Dartmouth', taunt: 'the Big Green in the woods' },
  { key: 'penn', label: 'Penn', taunt: 'the Quakers of Philadelphia' },
] as const
export type RivalKey = (typeof RIVALS)[number]['key']

export const rivalDan = (r: RivalKey, small = false) => `/media/dan/rival_${r}${small ? '_sm' : ''}.webp`
export const rivalLabel = (r: RivalKey) => RIVALS.find((x) => x.key === r)?.label ?? 'Rival'

const KEY = 'cc_visitor'

export function loadVisitor(): Visitor | null {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? 'null') as Visitor | null
    return v && VISITOR_CHOICES.some((c) => c.type === v.type) ? v : null
  } catch {
    return null
  }
}

export function saveVisitor(v: Visitor | null) {
  try {
    if (v) localStorage.setItem(KEY, JSON.stringify(v))
    else localStorage.removeItem(KEY)
  } catch {
    /* storage unavailable: the choice lasts for this page view */
  }
}

// One short sentence for the chat agent (sent with each message).
export function describeVisitor(v: Visitor | null): string | undefined {
  if (!v) return undefined
  switch (v.type) {
    case 'alum':
      return `Yale alumnus${v.decade ? ` from the ${v.decade}` : ''}`
    case 'student':
      return `current Yale student${v.label ? ` (${v.label})` : ''}`
    case 'family':
      return `family of a Yalie${v.label ? ` (shopping as/for: ${v.label})` : ''}`
    case 'friend':
      return 'friend of a Yalie, shopping for a gift'
    case 'rival':
      return `fan of a rival school${v.rival ? ` (${rivalLabel(v.rival)})` : ''}`
  }
}

// --- Free-text cues in the chat (Part E follow-up) -------------------------------------

// "start over", "go back to the first question", "restart"… → ask the welcome question again.
export const wantsStartOver = (text: string) =>
  /\b(start(ing)? (over|again|from scratch)|restart|(go|take me) back to (the )?(first|initial|beginning|start|opening)( question)?|from the (top|beginning)|first question again)\b/i.test(text)

// "I'm a rival", "we're rivals", "rival here" (without naming a school) → Dan asks which one.
export const saysRival = (text: string) =>
  /\b(i'?m|i am|we'?re|we are|as)\b[^.?!]{0,25}\brivals?\b|^\s*rivals?\b|\brival (here|fan|school)\b/i.test(text)

// Another Ivy named anywhere in a message → that rival's Dan image appears with the reply.
// "Brown" and "Penn" are only counted as schools in school-like phrases ("brown hoodie" is a color, Penn State isn't an Ivy).
const RIVAL_PATTERNS: [RivalKey, RegExp][] = [
  ['harvard', /\bharvard\b|\bcrimson\b(?=[^.?!]{0,20}\b(fan|fans|school|team|grad|alum))/i],
  ['princeton', /\bprinceton\b/i],
  ['columbia', /\bcolumbia (university|lions?|fan|grad|alum|student)s?\b|\b(at|from|go(es)? to|went to|going to|attend(s|ed)?|love) columbia\b/i],
  ['cornell', /\bcornell\b/i],
  ['dartmouth', /\bdartmouth\b/i],
  ['brown', /\bbrown (university|bears?|fan|grad|alum|student|school)s?\b|\b(at|from|go(es)? to|went to|going to|attend(s|ed)?|love|rival) brown\b/i],
  ['penn', /\bupenn\b|\b(university of pennsylvania|penn quakers?)\b|\bpenn\b(?!\s*state)(?=[^.?!]{0,20}\b(fan|fans|grad|alum|student|school|university|quakers?)\b)|\b(at|from|go(es)? to|went to|going to|attend(s|ed)?|love) penn\b(?!\s*state)/i],
]

// Is this message still about the rivalry? (an Ivy named, "rival", "rivalry", The Game, "beat …")
export const aboutRivals = (text: string) =>
  !!detectRival(text) || saysRival(text) || /\b(rivals?|rivalry|the game|beat (them|harvard|princeton)|ivy league|ivies)\b/i.test(text)

export function detectRival(text: string): RivalKey | null {
  return RIVAL_PATTERNS.find(([, re]) => re.test(text))?.[0] ?? null
}
