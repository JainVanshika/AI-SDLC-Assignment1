# Feature Specification: Expense and Budget Tracker

**Status**: Draft

**Input**: A small personal expense tracker for one person. They record expenses with an amount in rupees, a category, a date and an optional note; list and filter them; see monthly totals per category; set a monthly budget limit per category and get a warning when an expense takes a category over its limit; and edit or delete an expense. All data is kept in one JSON file. It is used as a library and from the command line. Money is always a whole number of paise, never a floating-point number.

## Terminology

- **Paise**: one hundredth of a rupee. Every amount is stored and calculated as a whole number of paise. INR 450.50 is 45050 paise.
- **Expense**: one recorded spend, with an `id`, an `amount_paise`, a `category`, a `date` and a `description`.
- **Category**: one of `food`, `travel`, `bills`, `other`. The list is fixed.
- **Date**: a calendar date written `YYYY-MM-DD`. The tracker never reads the clock, so a date is always supplied.
- **Month**: a calendar month written `YYYY-MM`. An expense belongs to the month of its date.
- **Budget**: a monthly limit in paise for one category. One budget per category, and it applies to every month.
- **Total**: the sum of `amount_paise` of the expenses of one category in one month.
- **Reference data**: the four expenses below, used by the acceptance criteria. Description is empty where blank.

| id | amount_paise | category | date | description |
|---|---|---|---|---|
| 1 | 45000 | food | 2026-11-10 | lunch |
| 2 | 12050 | food | 2026-11-12 | |
| 3 | 30000 | travel | 2026-11-15 | bus |
| 4 | 9999 | food | 2026-10-31 | snacks |

## User Scenarios & Testing

Stories are in priority order. P1 is the core, P2 builds on it. Each can be built and tested on its own. Every acceptance criterion has an ID (`AC-nnn`) that the tasks and tests cite, together with the requirement it checks.

### User Story 1 - Record and list expenses (Priority: P1)

A person adds an expense and sees it in a list. The list is the same every time they ask. This is the core of the tool, so it comes first, and it can be checked on its own with the reference data and the lists of valid and invalid inputs below.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-001 | Given an empty store, when I add amount `450.00`, category `food`, date `2026-11-10` and description `lunch`, then the result is expense `1` with `amount_paise` 45000, and it is saved. | FR-001, FR-002 |
| AC-002 | Given the result of AC-001, when I add `120.50`, `food`, `2026-11-12` with no description, then it is expense `2` with `amount_paise` 12050 and an empty description. | FR-001, FR-006 |
| AC-003 | The amounts `450` (45000), `450.5` (45050), `0.50` (50) and `10000000.00` (1,000,000,000) are accepted. `10000000.01` is refused with `invalid-amount`. | FR-002, FR-003 |
| AC-004 | The amounts `0`, `0.00`, `-5`, `abc`, `1e3`, `450.505`, `.5`, `450.`, `007`, `4 50` and the empty text are each refused with `invalid-amount`. | FR-002, FR-003 |
| AC-005 | Category `entertainment` and category `Food` (capital letter) are each refused with `invalid-category`. | FR-004 |
| AC-006 | The dates `2026-02-30`, `2026-13-01`, `10-11-2026`, `2026-1-5` and the empty text are each refused with `invalid-date`. `2028-02-29` is accepted and `2027-02-29` is refused. | FR-005 |
| AC-007 | A description of 100 characters is accepted. A description of 101 characters is refused with `invalid-description`. | FR-006 |
| AC-008 | When more than one input is wrong, only the first error is reported, checking the amount, then the category, then the date, then the description. Amount `0` with category `x` gives `invalid-amount`. Category `x` with date `bad` gives `invalid-category`. | FR-007 |
| AC-009 | When an add is refused, the stored data is unchanged and no expense number is used up. | FR-001, FR-007 |
| AC-010 | Given the reference data, when I list everything, then the order is 4, 1, 2, 3 (by date, oldest first). | FR-008 |
| AC-011 | Given two expenses on the same date, the one with the lower id comes first. | FR-008 |
| AC-012 | Given an empty store, or a filter that matches nothing, the list is empty and the call succeeds. | FR-008 |

### User Story 2 - Find expenses by category and month (Priority: P1)

A person narrows the list to one category, one month, or both.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-013 | Given the reference data, when I list category `food`, then I get 4, 1, 2. | FR-009 |
| AC-014 | Given the reference data, when I list month `2026-11`, then I get 1, 2, 3. | FR-010 |
| AC-015 | Given the reference data, when I list category `food` and month `2026-11`, then I get 1, 2. | FR-009, FR-010 |
| AC-016 | A filter category that is not in the list gives `invalid-category`. A month such as `2026-13`, `2026-1` or `Nov` gives `invalid-month`. | FR-009, FR-010 |

### User Story 3 - See monthly totals (Priority: P1)

A person sees how much was spent in a month, per category and overall.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-017 | Given the reference data, the totals for `2026-11` are food 57050, travel 30000, bills 0, other 0, overall 87050. | FR-011 |
| AC-018 | Given the reference data, the totals for `2026-10` are food 9999, travel 0, bills 0, other 0, overall 9999. The expense on `2026-10-31` is not in November. | FR-011 |
| AC-019 | A month with no expenses, `2026-12`, gives 0 for every category and 0 overall. | FR-011 |
| AC-020 | A month that is not `YYYY-MM` gives `invalid-month`. | FR-010, FR-011 |

### User Story 4 - Set a budget and get a warning (Priority: P2)

A person sets a monthly limit for a category and is warned, not blocked, when an expense takes the month over it.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-021 | When I set a `food` budget of `600.00`, the stored limit is 60000. Setting `food` again to `700.00` replaces it (70000). | FR-012 |
| AC-022 | A budget amount that breaks the amount rules (`0`, `-1`, `abc`) is refused with `invalid-amount`, and a category that is not in the list with `invalid-category`. | FR-012, FR-002 |
| AC-023 | Given the reference data and a `food` budget of 60000, when I add `food` 20.00 on `2026-11-20`, then the November food total is 59050 and there is no warning. When I then add `food` 50.00 on `2026-11-21`, the expense is saved and the result carries a `budget-exceeded` warning with category `food`, month `2026-11`, total 64050 and limit 60000. | FR-013 |
| AC-024 | Given the reference data and a `food` budget of 60000, when I add `food` 29.50 on `2026-11-20`, the total is exactly 60000 and there is no warning. When I then add `food` 0.01, the total is 60001 and there is a warning. | FR-013 |
| AC-025 | Given no budget for `travel`, adding any travel expense never gives a warning. | FR-013 |
| AC-026 | Given the reference data and a `food` budget of 60000, when I edit expense 2 to `150.00`, the total is 60000 and there is no warning. When I edit it to `150.01`, the total is 60001 and the edit is saved with a warning. | FR-013, FR-015 |
| AC-027 | Given the reference data and a `food` budget of 45000, adding `food` 1.00 on `2026-12-01` gives no warning, because December has no other food expense and only that month's total counts. | FR-013 |
| AC-028 | Given the reference data and a `food` budget of 60000, the budget status for `2026-11` shows `food` with limit 60000, spent 57050, remaining 2950, and shows no other category. After the spent amount reaches 64050, remaining is -4050. | FR-014 |

### User Story 5 - Correct or remove an expense (Priority: P2)

A person fixes a mistake or deletes an expense.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-029 | Given the reference data, when I edit expense 1 to amount `500.00`, then its amount is 50000 and its category, date, description and id are unchanged. | FR-015 |
| AC-030 | Each of the category, date and description of an expense can be changed on its own, and the same rules as for adding apply. | FR-015 |
| AC-031 | An edit that gives no field to change is refused with `nothing-to-change`. | FR-015 |
| AC-032 | An edit with an invalid value, for example amount `0`, is refused with `invalid-amount` and the expense is unchanged. | FR-015, FR-007 |
| AC-033 | An id such as `abc`, `0`, `-1` or `1.5` gives `invalid-id`. A valid id that does not exist, `99`, gives `not-found`. | FR-016 |
| AC-034 | Given the reference data, when I delete expense 2, then it no longer appears in the list or in the totals. | FR-016 |
| AC-035 | Given the reference data, when I delete expense 4 and then add a new expense, the new expense is number 5. Numbers are never reused. | FR-001, FR-016 |

### User Story 6 - Keep the data safe on disk (Priority: P2)

A person closes the tool and finds everything as it was.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-036 | Given the reference data saved to a file, when the tool starts again and lists everything, then the same four expenses, amounts and ids are returned. | FR-017 |
| AC-037 | Given a file that does not exist, the store is empty, and the first add creates the file. | FR-018 |
| AC-038 | Given a file that is not valid JSON, every operation fails with `storage-error`, and the file is not changed. | FR-018 |
| AC-039 | Given a file where an amount is not a whole number (`450.5`), or a category is not in the list, every operation fails with `storage-error`, and the file is not changed. | FR-018, FR-002 |
| AC-040 | When writing the file fails part-way, the previous contents of the file are unchanged and still load. | FR-019 |

### User Story 7 - Use it from the command line (Priority: P3)

A person runs each operation from the command line, as text or as JSON.

| ID | Acceptance criterion | Requirement |
|---|---|---|
| AC-041 | Every operation (add, list, edit, delete, totals, set budget, budget status) is available from the command line. | FR-020 |
| AC-042 | In text output, an amount of 12050 paise is shown as `120.50`. In JSON output, amounts are integers in paise, and the JSON equals the library result. | FR-020, FR-001 |
| AC-043 | Success exits with 0, including a success with a warning. Invalid input and `not-found` exit with 2. A `storage-error` exits with 3. Errors go to standard error as `error <code>: <message>` and nothing is written to standard output. | FR-021 |
| AC-044 | Running the same command twice on the same file gives the same output. Adding an expense with no date is refused with `invalid-date`; the tool never uses today's date. | FR-005, FR-022 |

### Edge Cases

- An amount typed with a comma (`1,000`), a rupee sign (`₹450`) or spaces is invalid, not guessed.
- An expense on the first or last day of a month belongs to that month only.
- A budget that is set after the expenses already exceed it warns only on the next add or edit, never on the budget being set.
- Deleting the last expense in a month leaves that month's totals at 0.
- Two expenses with the same amount, category, date and description are two expenses, not a duplicate.

## Requirements

### Functional Requirements

- **FR-001**: The system shall add an expense from an amount, a category, a date and an optional description, give it the next expense number (1, 2, 3, ...), save it, and return it. Expense numbers shall never be reused, even after a deletion.
- **FR-002**: The amount shall be [NEEDS CLARIFICATION: how is an amount typed: in rupees with up to two decimal places, such as 450.50, or in whole paise, such as 45050?]. It shall be converted to a whole number of paise without floating-point arithmetic, and stored as an integer.
- **FR-003**: The amount shall be more than 0 and at most 1,000,000,000 paise (INR 10,000,000.00). Anything else is refused with `invalid-amount`.
- **FR-004**: The category shall be exactly `food`, `travel`, `bills` or `other`, in lower case. Anything else is refused with `invalid-category`.
- **FR-005**: The date shall be a real calendar date written `YYYY-MM-DD`, and is always supplied. A missing or invalid date is refused with `invalid-date`. [NEEDS CLARIFICATION: may an expense be dated in the future? The tracker never reads the clock, so it cannot tell which dates are in the future unless a reference date is given.]
- **FR-006**: The description is optional, at most 100 characters. A longer one is refused with `invalid-description`.
- **FR-007**: When more than one input is invalid, only the first error is returned, checking the amount, then the category, then the date, then the description. A refused request changes nothing.
- **FR-008**: Listing shall return expenses ordered by date (oldest first) and then by expense number. It shall return an empty list, not an error, when there are none.
- **FR-009**: Listing shall be filterable by one category, using the same rule as FR-004.
- **FR-010**: Listing and totals shall be filterable by one month written `YYYY-MM`. A month that is not valid is refused with `invalid-month`. A category and a month together mean both must match.
- **FR-011**: The system shall return, for a month, the total in paise for each of the four categories (0 when there are none) and the overall total.
- **FR-012**: The system shall set a monthly budget limit, in paise, for one category, using the amount rules of FR-002 and FR-003. A new limit replaces the old one for that category.
- **FR-013**: When adding or editing an expense takes the total of its category in its month above the category's budget limit, the system shall still save the expense and shall return a warning `budget-exceeded` with the category, the month, the total and the limit. A total equal to the limit is not above it. A category with no budget never warns.
- **FR-014**: The system shall return a budget status for a month: for each category that has a budget, the limit, the amount spent and the remaining amount (limit minus spent, which can be negative).
- **FR-015**: The system shall edit an expense by number, changing any of the amount, category, date and description, with the same rules as for adding. An edit with nothing to change is refused with `nothing-to-change`. The expense number never changes.
- **FR-016**: The system shall delete an expense by number. An expense number shall be a whole number of 1 or more; any other text is refused with `invalid-id`, and a valid number that does not exist with `not-found`. [NEEDS CLARIFICATION: must a deletion be confirmed, for example with an extra `--yes` option, or does it happen at once?]
- **FR-017**: All expenses, budgets and the next expense number shall be kept in one JSON file. Reading the file back shall give exactly the same data.
- **FR-018**: A file that does not exist shall be treated as an empty store. A file that is not valid JSON, or that holds an amount that is not a whole number or a category that is not in the list, shall fail every operation with `storage-error`, and shall not be changed.
- **FR-019**: Saving shall not leave the file half written: if saving fails, the previous contents remain and can be loaded.
- **FR-020**: Every operation shall be available as a library function and as a command line operation. Output shall be readable text by default and JSON on request. In JSON, amounts are integers in paise; in text, they are shown in rupees with two decimals.
- **FR-021**: The command line shall exit with 0 on success (with or without a warning), 2 on invalid input or `not-found`, and 3 on `storage-error`. Errors shall go to standard error and nothing shall be written to standard output.
- **FR-022**: The result of an operation shall depend only on the stored data and the inputs. The system shall not read the clock, use random numbers, or use the network.

### Key Entities

- **Expense**: `id` (whole number, from 1), `amount_paise` (whole number), `category` (one of four), `date` (`YYYY-MM-DD`), `description` (text, up to 100 characters, may be empty).
- **Budget**: a category and its monthly limit in paise.
- **Store**: the expenses, the budgets and the next expense number, kept together in one file.
- **Warning**: a `budget-exceeded` notice with the category, month, total and limit.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every acceptance criterion (AC-001 to AC-044) is checked by at least one automated test that cites its ID, and all of those tests pass.
- **SC-002**: For 1,000 randomly generated sets of expenses, the monthly totals and the budget warnings match an independent check that uses integer arithmetic only, in 100% of the sets.
- **SC-003**: Listing or totalling 10,000 expenses completes in under 2 seconds on a typical laptop.
- **SC-004**: After a failed write, the previous file loads with exactly the same data, in 100% of the injected failures.
- **SC-005**: Branch coverage of the library is at least 90%.
- **SC-006**: The lint, security and secret checks of the constitution report no findings.
- **SC-007**: Every error code in FR-003 to FR-021 (`invalid-amount`, `invalid-category`, `invalid-date`, `invalid-description`, `invalid-month`, `invalid-id`, `not-found`, `nothing-to-change`, `storage-error`) is produced by at least one test.

## Assumptions

- There is one user and one local data file. The file's location can be chosen when the tool is run.
- The only currency is the Indian rupee. Amounts are never converted.
- The category list is fixed in this version. Adding categories is out of scope.
- A budget is one limit per category and applies to every month. Per-month budgets are out of scope.
- A month is a calendar month and an expense belongs to the month of its date. Times of day and time zones do not exist.
- Out of scope: other currencies, income, recurring expenses, import and export, receipts, sharing, accounts and passwords, a web page, and syncing between devices.
