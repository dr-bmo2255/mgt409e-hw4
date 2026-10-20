// Handsome Dan's lines for the website (Problem 10 Part C2). The agent's own replies get their
// catchphrases from backend/dan_voice.py; these are the fixed lines the page shows by itself.

export const pick = <T,>(list: readonly T[], avoid?: T): T => {
  const options = list.length > 1 && avoid !== undefined ? list.filter((x) => x !== avoid) : list
  return options[Math.floor(Math.random() * options.length)]
}

// Dan's opening line in the chat. A different one each time the chat starts.
export const DAN_GREETINGS = [
  '*wags entire back half* Handsome Dan here. Fetch you something in proper Yale blue?',
  '*trots over with a tennis ball* Welcome to Campus Customs, chum! What are we hunting for today?',
  "*looks up from a nap on Old Campus* Oh, splendid, a visitor! Hoodies, crewnecks, tees: I've modeled them all.",
  '*adjusts his little bow tie* Handsome Dan, at your service. Shopping for yourself or for a lucky Bulldog fan?',
  "*sniffs the air* I smell game-day gear. Tell me what you're after and I'll sniff it out.",
  '*snorts happily* Boola boola! Ask me about sizes, prices, or what to wear to The Game.',
  "*barks once, politely* Dan here. Need a gift for Mom, Dad or Grandpa? I know just the thing.",
  '*rolls over, then remembers he is on duty* Ahem. Welcome! What can this bulldog fetch for you?',
  '*paws at the door of 57 Broadway* Come in, come in! Want to see the newest Yale gear, or design your own Dan?',
] as const

// Shown in Dan's voice instead of a generic error when the chat can't reach the server or the internet.
export const DAN_ERRORS = [
  "*digs frantically* I seem to have trouble finding where I buried that. You're going to have to ask me again in a bit.",
  "*sniffs the router suspiciously* My nose can't pick up an internet connection. Check your Wi-Fi and toss me that question again?",
  '*flops down on Old Campus* Even a champion bulldog needs a signal. Give it a moment and try me again.',
  '*chases his tail looking for the internet* Lost the scent! Ask me once more in a minute.',
  '*barks at the Wi-Fi* The connection wandered off like a Harvard fan at halftime. Try again shortly.',
] as const

// Signature phrases (no more "quite right, old sport" on every page).
export const DAN_CATCHPHRASES = [
  'Boola boola!',
  'Splendid choice.',
  "Now that's proper Bulldog blue.",
  'Mother Yale would approve.',
  'Top-drawer stuff.',
  'Capital idea.',
  'Bully for you!',
  'Fit for The Game.',
  'Paws down, a winner.',
  "That's the Whiffenpoof spirit.",
  'Very Old Campus of you.',
  'Woof. Approved.',
] as const

// A stable catchphrase per item (so a product page doesn't change its quote on every render).
export function phraseFor(key: string): string {
  let h = 0
  for (const ch of key) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return DAN_CATCHPHRASES[h % DAN_CATCHPHRASES.length]
}

// A network failure (offline, server down) rather than a message the server chose to send.
export const isConnectionError = (err: unknown) => err instanceof TypeError || !navigator.onLine

// When a rival's Dan image goes up on the page (never in the chat), Dan nudges the shopper to look, subtly.
export const DAN_LOOK_UP = [
  '*glances meaningfully toward the top of the page*',
  '*tilts his head toward the top of the page* I may have left you a little something up there.',
  '*nudges the page with his nose* Something worth seeing up top, old sport.',
  '*wags in the general direction of the top of the page*',
]
export const BRAND_LOOK_UP = 'Handsome Dan left a little something for you at the top of the page.'
