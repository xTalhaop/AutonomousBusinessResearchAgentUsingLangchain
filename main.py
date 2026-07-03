from Agents.planner import run as planner
from Agents.cleaner import run as cleaner
from Agents.merger import run as merger
from Agents.final_report_generator import run as exporter

def main():
    topic = input("Enter business idea: ")

    print("=" * 60)
    print("STEP 1 : Planner Agent")
    print("=" * 60)
    planner(topic)

    print("=" * 60)
    print("STEP 2 : Cleaning Agent")
    print("=" * 60)
    cleaner()

    print("=" * 60)
    print("STEP 3 : Merge Agent")
    print("=" * 60)
    merger()

    print("=" * 60)
    print("STEP 4 : Report Generator")
    print("=" * 60)
    exporter()

    print("\nProject completed successfully.")

if __name__ == "__main__":
    main()