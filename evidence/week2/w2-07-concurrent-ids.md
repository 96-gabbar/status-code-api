# W2-07 Concurrency-Safe Public IDs

**Implementation date:** 6 November 2026
**Status:** DONE — parallel PostgreSQL verification passed

The initial migration creates `exception_id_seq` beginning at 10001. `SqlAlchemyExceptionRepository.next_exception_id()` obtains its value with PostgreSQL `nextval` through SQLAlchemy and formats it as `EXC-<digits>`. PostgreSQL sequences allocate unique values across sessions and are not rolled back, which is the intended identity behavior.

Unit coverage verifies the formatted result and rejects an absent database value. The live integration test created 20 exceptions concurrently through independent sessions and observed 20 unique `EXC-<digits>` values with no database errors or duplicate IDs.
