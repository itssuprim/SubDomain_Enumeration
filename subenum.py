import os
import subprocess
import argparse
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import mariadb
import pandas as pd

# Global variables for errors, results, and progress tracking
error_list = []
results_set = set()  # Set to track unique results
results_list = []
progress_bar = None
total_tools = 0
completed_tools = 0
start_time = time.time()

# Database connection configuration
db_config = {
    "user": "root",
    "password": "root",
    "database": "subdomain_tool"
}

def get_db_connection():
    """Get a MariaDB connection, trying localhost first, then 127.0.0.1."""
    try:
        db_config["host"] = "localhost"
        return mariadb.connect(**db_config)
    except mariadb.Error as e:
        if e.errno == mariadb.ER_ACCESS_DENIED_ERROR:
            print("[!] Access denied using localhost, trying 127.0.0.1...")
            db_config["host"] = "127.0.0.1"
            return mariadb.connect(**db_config)
        raise

def save_to_database(query, values):
    """Function to save data to the MariaDB database."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
    except mariadb.Error as err:
        print(f"[!] Database error: {err}")
        error_list.append(f"[!] Database error: {err}")

def parse_output_file(output_file, tool_name):
    """Parse the output file and remove duplicates."""
    global results_set, results_list
    try:
        with open(output_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and line not in results_set:
                    results_set.add(line)
                    results_list.append({"Tool": tool_name, "Result": line})
                    save_to_database(
                        "INSERT INTO results (tool_name, result) VALUES (%s, %s)",
                        (tool_name, line)
                    )
    except FileNotFoundError:
        error_message = f"[!] Output file not found: {output_file}"
        print(error_message)
        error_list.append(error_message)
        save_to_database("INSERT INTO errors (error_message) VALUES (%s)", (error_message,))

def run_tool(tool_config, target):
    """Run a tool command and process its output."""
    global error_list, completed_tools, progress_bar

    tool_name = tool_config["name"]
    command = tool_config["command"]
    output_file = tool_config["output_file"]
    output_type = tool_config["output_type"]

    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Handle output based on type
        if output_type == "stdout":
            if result.stdout.strip():
                with open(output_file, "w") as f:
                    f.write(result.stdout)
                print(f"[+] {tool_name} output saved to {output_file}")
                parse_output_file(output_file, tool_name)
            else:
                error_message = f"[!] {tool_name} produced no output."
                print(error_message)
                error_list.append(error_message)
                save_to_database("INSERT INTO errors (error_message) VALUES (%s)", (error_message,))
        elif output_type == "file":
            if os.path.exists(output_file):
                print(f"[+] {tool_name} output saved to {output_file}")
                parse_output_file(output_file, tool_name)
            else:
                error_message = f"[!] {tool_name} did not generate output file."
                print(error_message)
                error_list.append(error_message)
                save_to_database("INSERT INTO errors (error_message) VALUES (%s)", (error_message,))

        # Handle command errors
        if result.returncode != 0:
            error_message = f"[!] Error in {tool_name}:\n{result.stderr}"
            print(error_message)
            error_list.append(error_message)
            save_to_database("INSERT INTO errors (error_message) VALUES (%s)", (error_message,))

    except FileNotFoundError:
        error_message = f"[!] Command not found: {command.split()[0]}. Ensure the tool is installed and in your PATH."
        print(error_message)
        error_list.append(error_message)
        save_to_database("INSERT INTO errors (error_message) VALUES (%s)", (error_message,))
    except Exception as e:
        error_message = f"[!] Error running {tool_name}: {e}"
        print(error_message)
        error_list.append(error_message)
        save_to_database("INSERT INTO errors (error_message) VALUES (%s)", (error_message,))

    completed_tools += 1
    progress_bar.update(1)

def start_enumeration(domain, ip, output_dir):
    """Start the enumeration process using multiple tools."""
    global total_tools, completed_tools, progress_bar

    target = domain if domain else ip
    if not target:
        print("Error: Please provide either a domain or an IP address.")
        return

    os.makedirs(output_dir, exist_ok=True)

    commands = [
        {
            "name": "subfinder",
            "command": f"subfinder -d {target} -silent",
            "output_file": os.path.join(output_dir, f"subfinder_{target}.txt"),
            "output_type": "stdout"
        },
        {
            "name": "Sublist3r",
            "command": f"python3 /usr/bin/sublist3r -d {target} -o {os.path.join(output_dir, f'sublist3r_{target}.txt')}",
            "output_file": os.path.join(output_dir, f"sublist3r_{target}.txt"),
            "output_type": "file"
        },
        {
            "name": "assetfinder",
            "command": f"assetfinder --subs-only {target}",
            "output_file": os.path.join(output_dir, f"assetfinder_{target}.txt"),
            "output_type": "stdout"
        },
        {
            "name": "findomain",
            "command": f"findomain -t {target}",
            "output_file": os.path.join(output_dir, f"findomain_{target}.txt"),
            "output_type": "stdout"
        },
        {
            "name": "hakrawler",
            "command": f"echo {target} | docker run --rm -i hakluke/hakrawler -plain -depth 1 -scope subs",
            "output_file": os.path.join(output_dir, f"hakrawler_{target}.txt"),
            "output_type": "stdout"
        },
        {
            "name": "gau",
            "command": f"gau {target} --threads 20",
            "output_file": os.path.join(output_dir, f"gau_{target}.txt"),
            "output_type": "stdout"
        },
        {
            "name": "knockpy",
            "command": f"knockpy {target} --json --save {os.path.join(output_dir, f'knock_{target}')}",
            "output_file": os.path.join(output_dir, f"knock_{target}", f"{target}.json"),
            "output_type": "file"
        }
    ]

    total_tools = len(commands)
    completed_tools = 0
    progress_bar = tqdm(total=total_tools, desc="Running Tools", ncols=100, dynamic_ncols=True)

    with ThreadPoolExecutor(max_workers=8) as executor:
        for tool_config in commands:
            # Create output directory for knockpy if needed
            if tool_config["name"] == "knockpy":
                os.makedirs(os.path.dirname(tool_config["output_file"]), exist_ok=True)
            executor.submit(run_tool, tool_config, target)

    print("\n[+] Enumeration Complete.")

def remove_duplicates_and_export_to_excel(output_dir):
    """Remove duplicates and export results to Excel."""
    df = pd.DataFrame(results_list)
    df.drop_duplicates(subset="Result", inplace=True)
    excel_path = os.path.join(output_dir, "subdomain_enumeration_results.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"[+] Final results saved to {excel_path}")

def show_welcome_page():
    """Display the welcome page for the tool."""
    print("""
    ===============================================
    Welcome to the Subdomain Enumeration CLI Tool!
    ===============================================
    """)

def main():
    """Main function to handle CLI arguments and initiate processes."""
    show_welcome_page()

    parser = argparse.ArgumentParser(description="Subdomain Enumeration Tool")
    parser.add_argument("-d", "--domain", type=str, help="Domain name for subdomain enumeration")
    parser.add_argument("-i", "--ip", type=str, help="IP address for enumeration")
    parser.add_argument("-o", "--output", type=str, default="output", help="Output directory (default: output)")
    parser.add_argument("-r", "--recheck", type=str, help="Input file to recheck duplicates")

    args = parser.parse_args()

    if args.domain or args.ip:
        start_enumeration(args.domain, args.ip, args.output)
        remove_duplicates_and_export_to_excel(args.output)

    if args.recheck:
        remove_duplicates_and_export_to_excel(args.recheck)

if __name__ == "__main__":
    main()