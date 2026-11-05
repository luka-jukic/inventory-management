# Council result

Write the result in plain, short sentences. Every point must be clear without reading the chat.
Every "change" point shows what to change with a small before/after example.

## Layout

~~~markdown
# Council result: <PR title>

**Verdict:** ✅ ready to merge / ⚠️ merge after the must-changes / ❌ needs rework
**In short:** 1-2 sentences: does the PR do its job, and what is most important to change.

## Goals of the ticket

| Goal | Status | Proof |
|---|---|---|
| G1 Editor sees a red box when the form has no recipient | ✅ met | `InquiryBrick.php:40`, tested in editmode |
| G2 No inquiry is lost silently | ⚠️ partly | sends error status, but the confirmation mail goes out first (F1) |
| G3 Migration fixes the stored addresses | ✅ met | dry-run 257 changes, all with a real error |

(Goals from the ticket's acceptance criteria. If the ticket had none: "goals written from the ticket text".)

| | Count |
|---|---|
| Must change | 1 |
| Should change | 1 |
| Optional | 1 |
| Dropped | 1 |
| Follow-ups (not this PR) | 2 |

Reviewers: opus, fable, sonnet, haiku, OpenAI (gpt-…), Grok (skipped: not logged in) · Chat: <path>, 2 turns

---

## Must change

### F1 · Contact form crashes when the page has no mail template · score 7.5

**Where:** `src/EventListener/InquiryFormMailListener.php:23`

**Problem:** When the form brick has no mail template, `getById()` gets `null` and throws a `TypeError`.
The visitor sees "sent", but the message is lost.

**Why:** `$templateId` comes from the brick and can be empty. The check on line 18 only looks at the
recipient, not at the template.

**Change:**

```php
// before
$template = Document::getById($templateId);

// after
if (!$templateId) {
    $event->markFailed('no mail template');
    return;
}
$template = Document::getById($templateId);
```

**Test:** submit a form on a page without a template → error status, no TypeError in the log.

**Council:** agree opus, sonnet, OpenAI · disagree fable ("line 18 covers it"), changed to agree in turn 2
after R3 showed line 18 only checks the recipient.

---

## Should change

### F2 · … · score 4

(same parts: Where, Problem, Why, Change, Test, Council)

## Optional

### F3 · Rename `$tmp` to `$template` · score 1

**Where:** `…:30` · **Change:** `$tmp` → `$template`, it is used for 40 lines.

## Follow-ups (not part of this PR)

Real, but the PR did not cause them and the ticket did not ask for them. Do not block the merge.
Suggest a new ticket if worth it.

- **Inquiry form trusts the posted recipient field** (`InquiryController.php:61`): already there before
  this PR. Security, worth its own ticket.
- **Log message is German only** (`…:88`): nice to have.

## Dropped

- **F4** "Missing null check on line 51": not a problem, line 48 already returns when the object is
  missing (R3 showed it in turn 1, the finder dropped it).

## What is good

- The migration is reversible and has a dry-run.
~~~

## Rules

- **Title of a point** = what goes wrong, in words the PM also understands. No class names in the title.
- **Problem** = what happens for the user or the system. **Why** = the cause in the code.
- **Change** = the smallest code change that fixes the cause. Real code from the PR, shortened, with
  `// before` and `// after`. If the change is not code (config, data, docs), show the line or value.
- **Test** = one line: how to see it works.
- Optional points can be one line.
- **Dropped** points stay in the result with the reason, so the same idea is not raised again.
- Keep the order: Goals, Must, Should, Optional, Follow-ups, Dropped. Inside a group sort by score.
- **Verdict rule:** ✅ all goals met and no must-change. ⚠️ goals met or partly, must-changes are small.
  ❌ a goal is not met, or a must-change needs a redesign. Follow-ups never change the verdict.
- Must / Should / Optional only for points in scope of this PR. A finding the PR did not cause goes to
  Follow-ups, even when it is serious (then say so and suggest a ticket).
- No praise filler. "What is good" only with real points, max 3.
- When the user wants PR comments, every point (without the Council line) is one comment on its
  `file:line`.
