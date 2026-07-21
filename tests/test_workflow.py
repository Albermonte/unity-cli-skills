from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github/workflows/update-unity-cli.yml"


def test_refreshes_update_branch_before_force_with_lease() -> None:
    workflow = WORKFLOW.read_text()
    refresh = 'git fetch origin "refs/heads/${UPDATE_BRANCH}:refs/remotes/origin/${UPDATE_BRANCH}"'
    push = 'git push --force-with-lease origin "$UPDATE_BRANCH"'

    assert refresh in workflow
    assert workflow.index(refresh) < workflow.index(push)
