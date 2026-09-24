# TCP Protocol

The project uses a deliberately small text protocol over TCP. Each connection carries one request and one response.

## External client-to-main-server protocol

User command files are translated by `UserProcess` into the following requests.

| User command | Request sent to main server | Response |
| --- | --- | --- |
| `Register` | `register_user <user_name>` | `success <user_id>` or `failure` |
| `Register_book <title>` | `register_book <title>` | `success` or `failure` |
| `Lend <title>` | `lend_book <user_id> <title>` | `success` or `failure` |
| `Return <title>` | `return_book <user_id> <title>` | `success` or `failure` |
| `Sleep <seconds>` | No network request | No server response |

A user process stores the ID returned by `Register` in memory and uses it for later lend/return operations.

## Internal main-server-to-user-server protocol

The main server communicates with the user service on port `5001`.

| Request | Meaning | Response |
| --- | --- | --- |
| `register <name>` | Create a new user | `success <user_id>` or `failure` |
| `check <user_id>` | Validate a user ID | `success` or `failure` |

## Internal main-server-to-book-server protocol

The main server communicates with the book service on port `5002`.

| Request | Meaning | Response |
| --- | --- | --- |
| `register <title>` | Add a new book | `success` or `failure` |
| `lend <user_id> <title>` | Lend an available book | `success` or `failure` |
| `return <user_id> <title>` | Return a book held by that user | `success` or `failure` |

## Validation behavior

Before forwarding `lend_book` or `return_book` to the book service, the main server asks the user service to validate the supplied user ID.

The book service then applies its own state checks:

- Lending fails when the title does not exist or is already borrowed.
- Returning fails when the title does not exist or the requesting user is not the current borrower.
- Registering a user or book fails when the corresponding name/title already exists.

## Framing and size assumptions

The implementation performs a single `recv(1024)` call for each request or response. There is no length prefix, delimiter framing, streaming mode, or protocol negotiation.

That is sufficient for the short commands used by this project, but it is not intended as a production network protocol.