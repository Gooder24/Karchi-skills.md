#!/usr/bin/env bun
// Prefilled submit links for an idea up for adoption; Karchi reads the form and clicks Submit himself.
// bun adopcia/odkazy.ts <title> <url> <text> [subreddit]
const [title, url, text, sub = "SomebodyMakeThis"] = Bun.argv.slice(2);
if (!title || !url || !text) {
  console.error("usage: odkazy.ts <title> <url> <text> [subreddit]");
  process.exit(2);
}
if (!/^\w+$/.test(sub)) {
  console.error(`odkazy.ts: "${sub}" is not a subreddit name`);
  process.exit(2);
}
const hn = new URLSearchParams({ u: url, t: title });
const reddit = new URLSearchParams({ selftext: "true", title, text: `${text}\n\n${url}` });
console.log(`Hacker News: https://news.ycombinator.com/submitlink?${hn}`);
console.log(`r/${sub}: https://old.reddit.com/r/${sub}/submit?${reddit}`);
