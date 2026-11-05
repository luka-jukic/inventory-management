---
name: pr-council
description: Council review of a pull request. Claude agents (opus, fable, sonnet, haiku) plus OpenAI (codex CLI) and Grok (grok CLI) first review the PR on their own, then discuss the findings with each other in a shared chat. Findings are scored with a higher weight for Claude, the main thread moderates, checks the open points and writes one list of what to change. Use when the user asks for a council, a multi-model or second-opinion review, or wants to discuss what to change or adjust in a PR (Bitbucket, GitHub or a local branch).
---

# PR council

Several reviewers look at the same PR, each with a different model and a different focus. First they
review alone, so they do not copy each other. Then they discuss in a shared chat file: everyone reads
what the others wrote and answers them. You (the main thread) are the moderator: you pass the chat
around, stop it, check the open points in the code and write one clear list.

## First question: does the PR do its job?

The council answers two questions, in this order:

1. **Are the goals of the ticket met?** Take the acceptance criteria from the ticket. If there are none,
   write them from the ticket and PR description and say so. Each goal gets: met / partly / not met /
   cannot check, with proof.
2. **Does the PR break or risk something?** Only problems the PR **causes or touches**.

Everything else (old problems in the code around it, nice-to-haves, ideas the ticket did not ask for) is a
**follow-up**: listed separately, never blocks the merge. The verdict depends only on 1 and 2.

## Rules

- **Read-only.** No commits, no pushes, no PR comments, no approve or merge, unless the user asks.
  OpenAI and Grok also run read-only (see [EXTERNAL.md](EXTERNAL.md)).
- **Proof beats score.** A point counts only with `file:line` and a reason. The score sorts and breaks
  ties; if the code proves a high-score point wrong, it is dropped.
- Give the reviewers the code and the PR, not your opinion. As moderator you do not take sides in the chat.
- In the chat the reviewers are called R1-R6, not by model, so nobody follows a "big" model. Keep the
  mapping for yourself.
- Small PR (under ~50 changed lines): opus + fable + one external are enough. Tell the user the plan and
  the cost before a big council.
- If a CLI is missing or not logged in, skip that reviewer and say so in the result. Never block on it.

## Reviewers and weights

| Reviewer | How | Focus | Weight |
|---|---|---|---|
| Claude opus | `Agent`, `model: opus` | Does it work? Bugs, edge cases, null, missing callers, cause or only symptom | 3 |
| Claude fable | `Agent`, `model: fable` | Simpler way? Design, too much code, breaking changes, what hurts later | 3 |
| Claude sonnet | `Agent`, `model: sonnet` | Risk: security, data and migrations, deploy, performance, tests | 2 |
| Claude haiku | `Agent`, `model: haiku` | Project rules: coding style, naming, commit and PR format, docs | 1 |
| OpenAI | `codex exec` | Full review, no fixed focus | 1.5 |
| Grok | `grok -p` | Full review, no fixed focus | 1 |

**Score of a finding** = sum of the weights of everyone who found it or agrees at the end of the chat,
minus the weights of everyone who still disagrees with proof. "Not sure" counts 0.

## Steps

1. **Get the PR.** Title, description, ticket, target branch, full diff, and the changed files in full.
   Bitbucket: Atlassian MCP `getBitbucketRepoPullRequest` + `...Diff`; GitHub: `gh pr view` + `gh pr diff`;
   local: `git diff <base>...<branch>`. Read the linked ticket: reviewers must know what the PR should do.
   Write the goals list (acceptance criteria) into `<scratchpad>/council/goals.md`; every reviewer gets it.
   Check out the source branch in a worktree so all reviewers read the same code. Put diff, briefs and the
   chat file in `<scratchpad>/council/`.
2. **Round 1: review alone.** In one message: the Claude agents in the background (brief in
   [BRIEFS.md](BRIEFS.md) part 1) and the two CLIs as background Bash commands ([EXTERNAL.md](EXTERNAL.md)).
3. **Start the chat file.** First the goals with each reviewer's verdict (G1, G2, ...). Then merge the
   findings: same problem from several reviewers = one finding. Move findings marked "follow-up" to their
   own list; they do not go into the chat unless a reviewer says it blocks a goal.
   Number them F1, F2, ... and write them into `chat.md` (layout in [CHAT.md](CHAT.md)), with "found by R2, R5".
4. **Chat** (details in [CHAT.md](CHAT.md)):
   - **Turn 1:** all reviewers read `chat.md` and answer every goal where the verdicts differ and every finding: agree / disagree / not sure, with
     proof. They may add new findings.
   - **Turn 2 and 3:** only findings that are still open (someone disagrees or is not sure, or new ones).
     Everyone reads the whole chat and answers the others directly ("R3, line 38 does not cover …").
   - All reviewers answer in parallel in each turn. You append all answers, then start the next turn.
   - **Stop** a finding when everyone says agree or drop. Stop the chat when a turn brings nothing new or
     after turn 3.
5. **Score and check.** Compute the score per finding. Every finding still open after the chat, and every
   one only an external model supports, you check in the code yourself and decide. Run a test if that
   settles it. Write your decision with the reason into `chat.md` as `[moderator]`.
6. **Write the result** ([RESULT.md](RESULT.md)). Tell the user where `chat.md` is. Ask if you should post the result
   as PR comments or fix the points.

## Result

Layout and a full example in [RESULT.md](RESULT.md). In short: verdict and a count table first, then
every point with **Where**, **Problem**, **Why**, **Change** (before/after code), **Test** and **Council**
(who agreed, who disagreed). Order: Must change, Should change, Optional, Dropped. Plain words, so every
point can be pasted as a PR comment.
