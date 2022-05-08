# Database Replication

## Active replication

### Using atomic broadcast or consensus protocol
Using a consensus algorithm, like Raft, we're able to impose a total order over the set of client transactions. This way, we ensure that every replica executes the same transactions in the same exact order.
As a simplification, we're using the Maelstrom's _lin-tso_ service to impose a total order on the transactions. This service provides a stream of monotonically increasing integers, which we use to tag transactions. Each replica executes transactions with increasingly higher tags, never "skipping" tags.

#### Determinism
Active replication only works with deterministic transactions/ databases. Even if we have a total order over the set of transactions, non-deterministic transactions mean that two replicas might not obtain the same result for the same transaction (for example, one might commit it and the other abort it). Like so, even if two replicas execute the exact same transactions by the same order, they might still diverge.
By default, our database objects are non-deterministic. If we don't explicitly make them deterministic, our replicas might diverge, even when using the _lin-tso_ service to impose an order over transactions. Here's an example of a run, with non-deterministic databases, where replica n1 commits transaction 61 (this id corresponds to the _lin-tso_ tag given to the transaction) and replica n2 aborts it:

```

DEBUG:root:n1-19: updating 12: [1, 2, 3]
INFO:root:Commited transaction 61 ([['append', 12, 3], ['append', 11, 10], ['r', 11, None], ['r', 12, None]])
```

```

INFO:root:Running transaction 61 ([['append', 12, 3], ['append', 11, 10], ['r', 11, None], ['r', 12, None]])
DEBUG:root:n1-19: locking 11
DEBUG:root:n1-19: locking 12
INFO:root:n1-19: aborted
INFO:root:Aborted transaction 61
```

Replica n2 eventually appends 4 to the list corresponding to key 12, and the replicas diverge, resulting in a history with anomalies, as reported by the maelstrom analysis:

```

:anomalies {:incompatible-order ( ...
                                 {:key 12,
                                  :values [[1 2 3]
                                           [1 2 4]]}
                                  ...
```
