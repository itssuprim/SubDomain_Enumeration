# SubDomain_Enumeration
# Subdomain Enumeration CLI Tool

## Overview
The **Subdomain Enumeration CLI Tool** automates the discovery of subdomains for a given domain or IP address. It integrates multiple open-source enumeration tools, processes the results, and stores them in a MariaDB database. The tool efficiently removes duplicates and exports the final results into an Excel file.

## Features
- **Automated Subdomain Discovery** using multiple tools:
  - Sublist3r : Finds subdomains using search engines and brute force.
  - Subfinder : Fast Passsive subdomain enumeration via APIs.
  - Assetfinder : Scrapes various sources for subdomains. 
  - Findomain : Fast API-based subdomain discovery.
  - Knockpy : Brute forces subdomains with a wordlist.
  - Hakrawler : Crawls URLs, JS files and endpoints
  - Gau : Retrieves historical URLs from multiple sources.
- **Parallel Execution** with multithreading to speed up the enumeration process.
- **Database Integration** with MariaDB for storing results and error logs.
- **Error Handling & Logging** to track issues during execution.
- **Duplicate Removal** to ensure clean and unique results.
- **Excel Export** for easy report generation.
- **Docker Support** for containerized execution of tools.

## Installation
### Prerequisites
- **Python 3.x**
- **MariaDB** (for storing results)
- **Docker** (if running Assetfinder & Gau in a container)
- Required Python packages:
  ```bash
  pip install tqdm mariadb pandas openpyxl
  ```

### Clone the Repository
```bash
git clone https://github.com/yourusername/subdomain-enum-tool.git
cd subdomain-enum-tool
```

## Usage
### Run the Tool
```bash
python3 subenumtabsqldata.py -d example.com -o output
```
#### Command-line Options
| Option | Description |
|--------|-------------|
| `-d, --domain` | Target domain for enumeration |
| `-i, --ip` | Target IP for enumeration |
| `-o, --output` | Output directory (default: `output`) |
| `-r, --recheck` | Input file to remove duplicate results |

### Running Inside Docker
If Assetfinder and Gau are installed inside Docker, ensure you use the correct syntax:
```bash
docker run --rm assetfinder --subs-only example.com
```
```bash
docker run --rm gau example.com --threads 20 --json
```

## Database Configuration
Ensure MariaDB is installed and configured with the following credentials:
```json
{
  "user": "root",
  "password": "root",
  "database": "subdomain_tool",
  "host": "localhost"
}
```
Modify `db_config` in the script if needed.

## Output
- Subdomains are saved in the output directory.
- Data is stored in MariaDB.
- Final results are exported to `subdomain_enumeration_results.xlsx`.

## Troubleshooting
- **No output from Gau & Assetfinder?** Ensure Docker is running and the commands work manually.
- **ModuleNotFoundError for Pandas?** Run `pip install pandas`.
- **Database connection issues?** Verify MariaDB credentials and that the database exists.

## License
MIT License

## Contributing
Feel free to submit pull requests or report issues!

## Author
S Suprim Pandit - [LinkedIn/GitHub Profile]


