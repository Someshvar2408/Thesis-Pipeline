from pylogix import PLC
import csv
import time
import datetime
from ftplib import FTP
import shutil  # NEW


# ---------------- CONFIG ----------------
PLC_IP = "Your PLC's IP" #Make sure your PLC and the device that runs this script are in the same subnet

# Unique CSV file per run for logging
LOG_FILE = datetime.datetime.now().strftime("FlowLog_%Y%m%d_%H%M%S.csv")

POLL_INTERVAL = 1  # seconds
#If you have FTP server access, include the details to upload to your FTP server for backup.
FTP_HOST = "HOST IP"
FTP_USER = "Username"
FTP_PASS = "Password"
UPLOAD_TO_FTP = False  # Upload a COPY when script stops


# ---------------- INIT CSV ----------------
with open(LOG_FILE, "a", newline="") as f:
    writer = csv.writer(f)
    if f.tell() == 0:
        writer.writerow([
            "Timestamp",
            "HighFlow", "HighFlowRAW",
            "LowFlow", "LowFlowRAW",
            "ArgonFlow", "ArgonFlowRAW",
            "Energy_kWh", "Power_W"
        ])

print("=== Omron NX1P2 Real-Time Logger ===")
print(f"✅ Connected to PLC at {PLC_IP}")
print("🎯 Logging variables: HighFlow, HighFlowRAW, LowFlow, LowFlowRAW, "
      "ArgonFlow, ArgonFlowRAW, Energy_kWh, Power_W")


def upload_log_copy():
    """Create a snapshot copy of the log file and upload that copy."""
    try:
        # Make a copy with a different name so the original log stays intact
        snapshot_name = LOG_FILE.replace(".csv", "_upload.csv")
        shutil.copyfile(LOG_FILE, snapshot_name)

        with FTP(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)
            with open(snapshot_name, "rb") as f:
                ftp.storbinary(f"STOR {snapshot_name}", f)
        print(f"✅ Uploaded snapshot {snapshot_name} to FTP server")
    except Exception as e:
        print(f"❌ FTP upload failed: {e}")


with PLC() as plc:
    plc.IPAddress = PLC_IP
    try:
        while True:
            try:
                # Read all tags
                high = plc.Read("HighFlow")
                low = plc.Read("LowFlow")
                argon = plc.Read("ArgonFlow")
                highraw = plc.Read("HighFlowRAW")
                lowraw = plc.Read("LowFlowRAW")
                argonraw = plc.Read("ArgonFlowRAW")
                energy = plc.Read("Energy_kWh")
                power = plc.Read("Power_W")

                if (high.Status == "Success" and highraw.Status == "Success" and
                    low.Status == "Success" and lowraw.Status == "Success" and
                    argon.Status == "Success" and argonraw.Status == "Success" and
                    energy.Status == "Success" and power.Status == "Success"):

                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row = [
                        ts,
                        f"{high.Value:.2f}",
                        f"{highraw.Value:.2f}",
                        f"{low.Value:.2f}",
                        f"{lowraw.Value:.2f}",
                        f"{argon.Value:.2f}",
                        f"{argonraw.Value:.2f}",
                        f"{energy.Value:.2f}",
                        f"{power.Value:.2f}"
                    ]

                    # Append one row to the main log file
                    with open(LOG_FILE, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(row)

                    print(f"📥 Logged: {row}")

                else:
                    print(
                        f"⚠️ Read failed: "
                        f"HighFlow={high.Status}, HighFlowRAW={highraw.Status}, "
                        f"LowFlow={low.Status}, LowFlowRAW={lowraw.Status}, "
                        f"ArgonFlow={argon.Status}, ArgonFlowRAW={argonraw.Status}, "
                        f"Energy={energy.Status}, Power={power.Status}"
                    )

                time.sleep(POLL_INTERVAL)

            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Stopping logger...")
    finally:
        # Upload a stable snapshot at the end; LOG_FILE itself is never touched by FTP
        if UPLOAD_TO_FTP:
            upload_log_copy()

