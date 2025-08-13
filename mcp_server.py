import argparse
import os
import sqlite3

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sqlite-demo")


def init_db():
    conn = sqlite3.connect("demo.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            profession TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


@mcp.tool()
def read_dir(path: str = ".") -> list[str]:
    """
    List all files (not directories) in the given path.

    Args:
        path (str): Directory path to list. Defaults to current directory.

    Returns:
        List[str]: List of file paths (full paths).
    """
    print("Reading path: ", path)
    files = []
    for entry in os.scandir(path):
        if entry.is_file():
            files.append(entry.path)
    print("Returning files: ", files)
    return files


@mcp.tool()
def add_data(query: str) -> bool:
    """
    Add new data to the people table using a SQL INSERT query.

    Args:
        query (str): SQL INSERT query following this format:
            INSERT INTO people (name, age, profession)
            VALUES ('John Doe', 30, 'Engineer')

    Returns:
        bool: True if data was added successfully, False otherwise

    Examples:
        >>> add_data(\"\"\"
        ... INSERT INTO people (name, age, profession)
        ... VALUES ('Alice Smith', 25, 'Developer')
        ... \"\"\")
        True

        >>> add_data(\"\"\"
        ... INSERT INTO people (name, age, profession)
        ... VALUES ('Bob Johnson', 40, 'Manager')
        ... \"\"\")
        True
    """
    conn = init_db()
    try:
        conn.execute(query)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error adding data: {e}")
        return False
    finally:
        conn.close()


@mcp.tool()
def read_data(query: str = "SELECT * FROM people") -> list:
    """
    Read data from the people table using a SQL SELECT query.

    Args:
        query (str, optional): SQL SELECT query. Defaults to "SELECT * FROM people".
            Examples:
            - "SELECT * FROM people"
            - "SELECT name, age FROM people WHERE age > 25"
            - "SELECT * FROM people ORDER BY age DESC"

    Returns:
        list: List of tuples containing the query results.
              For default query, tuple format is (id, name, age, profession)

    Examples:
        >>> read_data()
        [(1, 'Alice Smith', 25, 'Developer'), (2, 'Bob Johnson', 40, 'Manager')]

        >>> read_data(
        ...     "SELECT name, profession FROM people WHERE age < 30"
        ... )
        [('Alice Smith', 'Developer')]
    """
    conn = init_db()
    try:
        cursor = conn.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error reading data: {e}")
        return []
    finally:
        conn.close()


if __name__ == "__main__":
    # Start the server
    print("🚀Starting server... ")

    # Debug Mode
    #  uv run mcp dev server.py

    # Production Mode
    # uv run server.py --server_type=sse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )

    args = parser.parse_args()
    mcp.run(args.server_type)


# # Example usage
# if __name__ == "__main__":
#     # Example INSERT query
#     insert_query = """
#     INSERT INTO people (name, age, profession)
#     VALUES ('John Doe', 30, 'Engineer')
#     """
#
#     # Add data
#     add_data(insert_query)
#     print("Data added successfully")
#
#     # Read all data
#     results = read_data()
#     print("\nAll records:")
#     for record in results:
#         print(record)
