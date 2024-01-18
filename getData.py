import sys
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import csv

BITBUCKET_HOST_URL = "https://bitbucket-url"
BITBUCKET_URL = f"{BITBUCKET_HOST_URL}/rest/api/1.0"

def make_api_call(url, username, password, params=None):
    response = requests.get(url, auth=HTTPBasicAuth(username, password), params=params)
    #response.raise_for_status()
    return response.json() if response else None

def get_projects(username, password):
    projects_url = f"{BITBUCKET_URL}/projects"
    params = {"limit": 1000}
    return make_api_call(projects_url, username, password, params)["values"]

def get_repositories(username, password, project_key):
    repositories_url = f"{BITBUCKET_URL}/projects/{project_key}/repos"
    params = {"limit": 1000}
    return make_api_call(repositories_url, username, password, params)["values"]

def get_repository_size(username, password, project_key, repo_slug):
    size_url = f"{BITBUCKET_HOST_URL}/projects/{project_key}/repos/{repo_slug}/sizes"
    size_info = make_api_call(size_url, username, password)
    return size_info.get("repository", "N/A") // (1024 * 1024)

def get_files_in_repository(username, password, project_key, repo_slug):
    source_url = f"{BITBUCKET_URL}/projects/{project_key}/repos/{repo_slug}/browse"
    params = {"limit": 1000}
    source_info = make_api_call(source_url, username, password, params)
    return [file_info["path"]["toString"].lower() for file_info in source_info["children"]["values"]] if source_info else None

def get_commits_info(username, password, project_key, repo_slug):
    commits_url = f"{BITBUCKET_URL}/projects/{project_key}/repos/{repo_slug}/commits"
    params = {"limit": 1000}
    response = make_api_call(commits_url, username, password, params)
    return response.get("values", []) if response else []

def get_latest_commit_info(username, password, project_key, repo_slug):
    commits_url = f"{BITBUCKET_URL}/projects/{project_key}/repos/{repo_slug}/commits"
    params = {"limit": 1, "order": "newest"}
    response = make_api_call(commits_url, username, password, params)
    latest_commits = response.get("values", "N/A") if response else None
    return datetime.fromtimestamp(latest_commits[0]["authorTimestamp"] / 1000.0).strftime('%Y-%m-%d') if latest_commits else None

def get_branches_info(username, password, project_key, repo_slug):
    branches_url = f"{BITBUCKET_URL}/projects/{project_key}/repos/{repo_slug}/branches"
    params = {"limit": 1000}
    return make_api_call(branches_url, username, password, params)["values"]

def repository_has_file(files, file_pattern):
    return any(file_pattern.lower() in file.lower() for file in files) if files else 0

def write_to_csv(filename, data, file_patterns):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ["Project Name", "Repository Name", "Repository Size (MB)", "Number of Commits",
                  "Latest Commit Date", "Number of Branches"]
        for file_pattern in file_patterns:
            header.append(f"Has {file_pattern} Files")
        writer.writerow(header)
        writer.writerows(data)

def main(username, password, output_csv="output.csv"):
    data = []
    projects = get_projects(username, password)
    file_patterns = [".java", ".gradle", "pom.xml", "jenkinsfile", "Dockerfile"]

    for project in projects:
        project_key = project["key"]
        repositories = get_repositories(username, password, project_key)

        for repo in repositories:
            repo_slug = repo["slug"]
            repo_data = [project["name"], repo["name"], get_repository_size(username, password, project_key, repo_slug),
                         len(get_commits_info(username, password, project_key, repo_slug)),
                         get_latest_commit_info(username, password, project_key, repo_slug),
                         len(get_branches_info(username, password, project_key, repo_slug))]
            files_in_repository = get_files_in_repository(username, password, project_key, repo_slug)

            for file_pattern in file_patterns:
                repo_data.append(repository_has_file(files_in_repository, file_pattern))
            print(repo_data)
            data.append(repo_data)

    write_to_csv(output_csv, data, file_patterns)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <username> <password> [output_csv]")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    output_csv = "output.csv" if len(sys.argv) == 3 else sys.argv[3]

    main(username, password, output_csv)
