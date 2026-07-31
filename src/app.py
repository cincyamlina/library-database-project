import sqlite3
from datetime import date, timedelta
from pathlib import Path

DATABASE_NAME = Path(__file__).resolve().parent / "library.db"


def connect_database():
    """Create and return a database connection."""
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def print_rows(rows, empty_message="No records found."):
    """Print sqlite rows in a readable form."""
    rows = list(rows)

    if not rows:
        print(empty_message)
        return

    for row in rows:
        print(" | ".join(f"{key}: {row[key]}" for key in row.keys()))


def view_all_books():
    """Display every book and its author."""
    with connect_database() as connection:
        rows = connection.execute("""
            SELECT
                Books.book_id AS "Book ID",
                Books.title AS "Title",
                Authors.first_name || ' ' || Authors.last_name AS "Author",
                Books.publication_year AS "Year",
                Books.total_copies AS "Total Copies",
                Books.available_copies AS "Available Copies"
            FROM Books
            JOIN Authors
                ON Books.author_id = Authors.author_id
            ORDER BY Books.title
        """).fetchall()

    print("\nAll Books")
    print("-" * 90)
    print_rows(rows, "No books were found.")


def view_available_books():
    """Display books with at least one available copy."""
    with connect_database() as connection:
        rows = connection.execute("""
            SELECT
                Books.book_id AS "Book ID",
                Books.title AS "Title",
                Authors.first_name || ' ' || Authors.last_name AS "Author",
                Books.available_copies AS "Available Copies"
            FROM Books
            JOIN Authors
                ON Books.author_id = Authors.author_id
            WHERE Books.available_copies > 0
            ORDER BY Books.title
        """).fetchall()

    print("\nAvailable Books")
    print("-" * 80)
    print_rows(rows, "No books are currently available.")


def view_members():
    """Display all registered members."""
    with connect_database() as connection:
        rows = connection.execute("""
            SELECT
                member_id AS "Member ID",
                first_name || ' ' || last_name AS "Name",
                email AS "Email",
                phone AS "Phone",
                membership_date AS "Membership Date"
            FROM Members
            ORDER BY last_name, first_name
        """).fetchall()

    print("\nMembers")
    print("-" * 90)
    print_rows(rows, "No members were found.")


def view_authors():
    """Display all authors."""
    with connect_database() as connection:
        rows = connection.execute("""
            SELECT
                author_id AS "Author ID",
                first_name || ' ' || last_name AS "Name"
            FROM Authors
            ORDER BY last_name, first_name
        """).fetchall()

    print("\nAuthors")
    print("-" * 60)
    print_rows(rows, "No authors were found.")


def add_author():
    """Add an author and return the new author ID."""
    first_name = input("Enter the author's first name: ").strip()
    last_name = input("Enter the author's last name: ").strip()

    if not first_name or not last_name:
        print("Both first and last name are required.")
        return None

    try:
        with connect_database() as connection:
            cursor = connection.execute("""
                INSERT INTO Authors (first_name, last_name)
                VALUES (?, ?)
            """, (first_name, last_name))
            author_id = cursor.lastrowid

        print(f"Author added successfully with ID {author_id}.")
        return author_id
    except sqlite3.IntegrityError:
        print("That author already exists.")
        return None


def add_book():
    """Add a new book to the database."""
    view_authors()

    title = input("\nEnter book title: ").strip()
    isbn = input("Enter ISBN: ").strip()

    try:
        publication_year_text = input(
            "Enter publication year, or leave blank: "
        ).strip()
        publication_year = (
            int(publication_year_text)
            if publication_year_text
            else None
        )
        total_copies = int(input("Enter total number of copies: "))
        author_id = int(input("Enter author ID: "))
    except ValueError:
        print("Publication year, copies, and author ID must be valid numbers.")
        return

    if not title or not isbn:
        print("Title and ISBN are required.")
        return

    if total_copies < 0:
        print("Total copies cannot be negative.")
        return

    try:
        with connect_database() as connection:
            connection.execute("""
                INSERT INTO Books (
                    title,
                    isbn,
                    publication_year,
                    total_copies,
                    available_copies,
                    author_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                title,
                isbn,
                publication_year,
                total_copies,
                total_copies,
                author_id
            ))

        print("Book added successfully.")
    except sqlite3.IntegrityError as error:
        print(f"Unable to add book: {error}")


def register_member():
    """Register a new library member."""
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()
    email = input("Enter email address: ").strip()
    phone = input("Enter phone number, or leave blank: ").strip()

    if not first_name or not last_name or not email:
        print("First name, last name, and email are required.")
        return

    try:
        with connect_database() as connection:
            cursor = connection.execute("""
                INSERT INTO Members (
                    first_name,
                    last_name,
                    email,
                    phone,
                    membership_date
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                first_name,
                last_name,
                email,
                phone or None,
                date.today().isoformat()
            ))

        print(f"Member registered successfully with ID {cursor.lastrowid}.")
    except sqlite3.IntegrityError:
        print("A member with that email address already exists.")


def check_out_book():
    """Create a loan and decrease the available-copy count."""
    view_members()
    view_available_books()

    try:
        member_id = int(input("\nEnter member ID: "))
        book_id = int(input("Enter book ID: "))
    except ValueError:
        print("Member ID and book ID must be numbers.")
        return

    checkout_date = date.today()
    due_date = checkout_date + timedelta(days=14)

    try:
        with connect_database() as connection:
            member = connection.execute("""
                SELECT member_id
                FROM Members
                WHERE member_id = ?
            """, (member_id,)).fetchone()

            if member is None:
                print("The selected member does not exist.")
                return

            book = connection.execute("""
                SELECT title, available_copies
                FROM Books
                WHERE book_id = ?
            """, (book_id,)).fetchone()

            if book is None:
                print("The selected book does not exist.")
                return

            if book["available_copies"] <= 0:
                print("That book is not currently available.")
                return

            connection.execute("""
                INSERT INTO Loans (
                    member_id,
                    book_id,
                    checkout_date,
                    due_date,
                    return_date
                )
                VALUES (?, ?, ?, ?, NULL)
            """, (
                member_id,
                book_id,
                checkout_date.isoformat(),
                due_date.isoformat()
            ))

            connection.execute("""
                UPDATE Books
                SET available_copies = available_copies - 1
                WHERE book_id = ?
            """, (book_id,))

        print(f'"{book["title"]}" checked out successfully.')
        print(f"Due date: {due_date.isoformat()}")
    except sqlite3.IntegrityError as error:
        print(f"Unable to check out book: {error}")


def view_active_loans():
    """Display loans that have not been returned."""
    with connect_database() as connection:
        rows = connection.execute("""
            SELECT
                Loans.loan_id AS "Loan ID",
                Members.first_name || ' ' || Members.last_name AS "Member",
                Books.title AS "Book",
                Loans.checkout_date AS "Checkout Date",
                Loans.due_date AS "Due Date"
            FROM Loans
            JOIN Members
                ON Loans.member_id = Members.member_id
            JOIN Books
                ON Loans.book_id = Books.book_id
            WHERE Loans.return_date IS NULL
            ORDER BY Loans.due_date
        """).fetchall()

    print("\nActive Loans")
    print("-" * 100)
    print_rows(rows, "There are no active loans.")


def return_book():
    """Record a return and increase the available-copy count."""
    view_active_loans()

    try:
        loan_id = int(input("\nEnter loan ID: "))
    except ValueError:
        print("Loan ID must be a number.")
        return

    with connect_database() as connection:
        loan = connection.execute("""
            SELECT Loans.book_id, Books.title, Loans.return_date
            FROM Loans
            JOIN Books
                ON Loans.book_id = Books.book_id
            WHERE Loans.loan_id = ?
        """, (loan_id,)).fetchone()

        if loan is None:
            print("The selected loan does not exist.")
            return

        if loan["return_date"] is not None:
            print("This book has already been returned.")
            return

        connection.execute("""
            UPDATE Loans
            SET return_date = ?
            WHERE loan_id = ?
        """, (date.today().isoformat(), loan_id))

        connection.execute("""
            UPDATE Books
            SET available_copies = available_copies + 1
            WHERE book_id = ?
        """, (loan["book_id"],))

    print(f'"{loan["title"]}" returned successfully.')


def view_member_history():
    """Display all loans for one member."""
    view_members()

    try:
        member_id = int(input("\nEnter member ID: "))
    except ValueError:
        print("Member ID must be a number.")
        return

    with connect_database() as connection:
        member = connection.execute("""
            SELECT first_name, last_name
            FROM Members
            WHERE member_id = ?
        """, (member_id,)).fetchone()

        if member is None:
            print("The selected member does not exist.")
            return

        rows = connection.execute("""
            SELECT
                Loans.loan_id AS "Loan ID",
                Books.title AS "Book",
                Loans.checkout_date AS "Checkout Date",
                Loans.due_date AS "Due Date",
                COALESCE(Loans.return_date, 'Not returned') AS "Return Date"
            FROM Loans
            JOIN Books
                ON Loans.book_id = Books.book_id
            WHERE Loans.member_id = ?
            ORDER BY Loans.checkout_date DESC
        """, (member_id,)).fetchall()

    print(f'\nBorrowing History for {member["first_name"]} {member["last_name"]}')
    print("-" * 100)
    print_rows(rows, "This member has no borrowing history.")


def search_books():
    """Search for books by title or author."""
    search_term = input("Enter a title or author name: ").strip()

    if not search_term:
        print("Search text cannot be empty.")
        return

    pattern = f"%{search_term}%"

    with connect_database() as connection:
        rows = connection.execute("""
            SELECT
                Books.book_id AS "Book ID",
                Books.title AS "Title",
                Authors.first_name || ' ' || Authors.last_name AS "Author",
                Books.available_copies AS "Available Copies"
            FROM Books
            JOIN Authors
                ON Books.author_id = Authors.author_id
            WHERE Books.title LIKE ?
               OR Authors.first_name LIKE ?
               OR Authors.last_name LIKE ?
            ORDER BY Books.title
        """, (pattern, pattern, pattern)).fetchall()

    print("\nSearch Results")
    print("-" * 80)
    print_rows(rows, "No matching books were found.")


def display_menu():
    """Display the command-line menu."""
    while True:
        print("\nLibrary Management Database")
        print("1. View all books")
        print("2. View available books")
        print("3. Search books")
        print("4. Add a new author")
        print("5. Add a new book")
        print("6. View members")
        print("7. Register a new member")
        print("8. Check out a book")
        print("9. View active loans")
        print("10. Return a book")
        print("11. View member borrowing history")
        print("12. Exit")

        choice = input("Select an option: ").strip()

        actions = {
            "1": view_all_books,
            "2": view_available_books,
            "3": search_books,
            "4": add_author,
            "5": add_book,
            "6": view_members,
            "7": register_member,
            "8": check_out_book,
            "9": view_active_loans,
            "10": return_book,
            "11": view_member_history
        }

        if choice == "12":
            print("Goodbye.")
            break

        action = actions.get(choice)

        if action is None:
            print("Invalid selection. Enter a number from 1 through 12.")
        else:
            try:
                action()
            except sqlite3.Error as error:
                print(f"Database error: {error}")


if __name__ == "__main__":
    if not DATABASE_NAME.exists():
        print(
            f"Database file not found: {DATABASE_NAME}\n"
            "Place library.db in the same folder as app.py."
        )
    else:
        display_menu()
