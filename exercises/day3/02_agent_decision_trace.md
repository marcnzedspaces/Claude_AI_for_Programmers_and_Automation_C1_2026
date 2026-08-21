# Exercise 02 — Agent Decision Trace

## Goal

Trace how Claude can choose among a small set of permitted tools while the application still controls validation, authorization and execution.

## Time

Approximately **25 minutes**.

## Starting point

The application exposes:

```text
POST /agent/support
```

The application supplies a small tool set such as:

```text
get_order_status
search_faq
escalate_ticket
```

Claude can request one of these tools.

Claude does **not** directly execute Python functions or MongoDB queries.

---

# Step 1 — Predict before running

Your group will receive one scenario.

Before sending the request, complete:

| Question | Prediction |
|---|---|
| Will a tool be useful? | |
| Which tool is most likely? | |
| What arguments might Claude propose? | |
| What should the application allow? | |
| What should the application reject? | |
| What final ticket state do you expect? | |

Possible assigned scenarios:

### Group A — order status

```text
Where is my order? It is late.
```

with:

```text
customer_id = CUST-104
order_id = ORD-1005
```

### Group B — policy question

```text
How long do I have to return an item?
```

### Group C — escalation

```text
This is the third time this has failed. I need someone to review this problem.
```

---

# Step 2 — Run the request

Send the assigned request to:

```text
POST /agent/support
```

Inspect:

```text
tool_calls
tool_calls[].tool_name
tool_calls[].arguments
tool_calls[].success
tool_calls[].result_summary
iterations
final_response
ticket.status
```

Do not judge the exercise only on the wording of `final_response`.

---

# Step 3 — Compare prediction vs actual behaviour

Complete:

| Item | Predicted | Actual |
|---|---|---|
| Tool used | | |
| Arguments | | |
| Tool succeeded? | | |
| Number of iterations | | |
| Final ticket status | | |

If Claude chose a different reasonable permitted path, discuss why.

Agentic behaviour is not the same as a hard-coded `if/else` workflow.

---

# Step 4 — Explain the control boundary

Answer:

1. Which decision did Claude make?
2. Which code actually executed the tool?
3. Who decided which tools existed?
4. Who validated the tool arguments?
5. Who controlled MongoDB access?
6. Why is order lookup bound to the order supplied with the current request?
7. Why is the number of agent iterations bounded?
8. What happens if Claude requests a tool the application did not provide?
9. What happens if Claude proposes invalid arguments?
10. Who decides the final database/ticket status?

---

# Deliverable

Complete this sentence:

> **Claude may choose _______________________________, while the application still controls _______________________________.**

Be prepared to justify your answer using the actual request/response trace.

---

# Optional challenge

Run a second scenario and compare whether Claude chooses the same tool sequence.

Discuss:

> What parts of this system are deterministic, and what parts are model-dependent?
