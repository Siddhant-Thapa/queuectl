# test_executor.py
from queuectl.executor import execute_command

# Successful command
code, out, err = execute_command("echo Hello Executor")
print("Exit Code:", code)
print("STDOUT:", out)
print("STDERR:", err)

# Failing command
code, out, err = execute_command("nonexistent_command_xyz")
print("\nExit Code:", code)
print("STDOUT:", out)
print("STDERR:", err)

# Timeout example
code, out, err = execute_command("ping 127.0.0.1 -n 10 >nul", timeout=2)
print("\nExit Code:", code)
print("STDOUT:", out)
print("STDERR:", err)
