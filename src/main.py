import os
import getpass
import logging
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, AuthenticationException, SSHException
from ntc_templates.parse import parse_output

# Configure logging to write directly to logs/lab.log
logging.basicConfig(
    filename='logs/lab.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    # Log lab start markers (Step 1 & Step 2 requirements)
    logging.info("LAB2_START")
    logging.info("[STEP 2] Dev Container Started")

    # Ensure required output directories exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)

    # Step 3: Securely prompt for credentials
    print("--- Cisco DevNet Sandbox Authentication ---")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    logging.info("CREDENTIALS_COLLECTED")

    # Step 4: Configure device connection details
    device = {
        "device_type": "cisco_ios",
        "host": "devnetsandboxiosxec8k.cisco.com",  # Update host if assigned a specific sandbox IP
        "username": username,
        "password": password,
        "port": 22,
        "timeout": 20
    }

    try:
        print("Connecting to network device...")
        net_connect = ConnectHandler(**device)
        logging.info("CONNECT_OK")
        print("Connection successful!")
    except (AuthenticationException, NetmikoTimeoutException, SSHException) as e:
        logging.error(f"CONNECT_FAIL: {str(e)}")
        print(f"Connection failed: {e}")
        logging.info("LAB2_END")
        return

    # Step 5 & 6: Execute commands and parse outputs
    commands = [
        "show version",
        "show ip interface brief",
        "show inventory"
    ]

    for cmd in commands:
        logging.info(f"CMD_RUN:{cmd}")
        raw_output = net_connect.send_command(cmd)

        # Save raw terminal output
        file_name = cmd.replace(" ", "_") + ".txt"
        with open(f"data/raw/{file_name}", "w") as f:
            f.write(raw_output)

        # Parse output using ntc-templates
        try:
            parsed_data = parse_output(platform=device["device_type"], command=cmd, data=raw_output)
            if parsed_data:
                logging.info(f"PARSE_OK:{cmd}")
            else:
                logging.warning(f"PARSE_EMPTY:{cmd}")
        except Exception as parse_err:
            logging.error(f"PARSE_FAIL:{cmd} - {parse_err}")

    # Close SSH session
    net_connect.disconnect()

    # Step 7: Generate Report Summary
    summary_text = f"""
========================================
       LAB 2 DEVICE SUMMARY REPORT
========================================
Target Device : {device['host']}
Device Type   : {device['device_type']}
Status        : Commands successfully executed and parsed.
========================================
"""
    print(summary_text)

    with open("data/reports/device_summary.txt", "w") as report_file:
        report_file.write(summary_text)

    logging.info("REPORT_SAVED")

    # Step 8: End Marker
    logging.info("LAB2_END")
    print("Lab 2 completed successfully.")

if __name__ == "__main__":
    main()