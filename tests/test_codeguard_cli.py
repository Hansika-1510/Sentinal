import subprocess
import sys
import os
import tempfile
from click.testing import CliRunner
from cli.devguard import cli


def test_devguard_cli_blocks_secrets():
    runner = CliRunner()
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".diff") as f:
        f.write("""diff --git a/config.env b/config.env
new file mode 100644
--- /dev/null
+++ b/config.env
@@ -0,0 +1,1 @@
+AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLEKEY
""")
        temp_path = f.name

    try:
        result = runner.invoke(cli, ["review-staged", "--diff-file", temp_path])
        assert result.exit_code == 1
        assert "COMMIT BLOCKED" in result.output
    finally:
        os.remove(temp_path)


def test_devguard_cli_passes_clean_diff():
    runner = CliRunner()
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".diff") as f:
        f.write("""diff --git a/Readme.md b/Readme.md
--- a/Readme.md
+++ b/Readme.md
@@ -1,1 +1,1 @@
-Hello
+Hello World
""")
        temp_path = f.name

    try:
        result = runner.invoke(cli, ["review-staged", "--diff-file", temp_path])
        assert result.exit_code == 0
        assert "COMMIT PASSED" in result.output
    finally:
        os.remove(temp_path)
