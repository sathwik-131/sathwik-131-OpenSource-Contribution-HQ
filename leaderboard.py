import json
import os

DATA_FILE = "participants.json"

POINTS = {
    "features": 10,
    "bug_fixes": 5,
    "documentation": 2,
    "tests": 4
}


# Load existing data
def load_data():

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)

    return [
        {
            "name": "Sathwik",
            "contributions": {
                "features": 3,
                "bug_fixes": 2,
                "documentation": 1,
                "tests": 2
            }
        },
        {
            "name": "Rahul",
            "contributions": {
                "features": 1,
                "bug_fixes": 4,
                "documentation": 2,
                "tests": 1
            }
        },
        {
            "name": "Arjun",
            "contributions": {
                "features": 2,
                "bug_fixes": 1,
                "documentation": 5,
                "tests": 3
            }
        }
    ]


participants = load_data()


# Save data
def save_data():

    with open(DATA_FILE, "w") as file:
        json.dump(participants, file, indent=4)


# Calculate score
def calculate_score(contributions):

    score = 0

    for category, count in contributions.items():
        score += POINTS[category] * count

    return score


# Add participant
def add_participant():

    name = input("\nEnter participant name: ").strip()

    if not name:
        print("Name cannot be empty!")
        return

    if any(p["name"].lower() == name.lower() for p in participants):
        print("Participant already exists!")
        return

    participants.append({
        "name": name,
        "contributions": {
            "features": 0,
            "bug_fixes": 0,
            "documentation": 0,
            "tests": 0
        }
    })

    save_data()

    print(f"\n{name} added successfully!")


# Add contribution
def add_contribution():

    name = input("\nEnter participant name: ").strip()

    participant = next(
        (p for p in participants if p["name"].lower() == name.lower()),
        None
    )

    if participant is None:
        print("Participant not found!")
        return

    print("\nContribution Categories:")

    for category in POINTS:
        print(f"- {category}")

    category = input("\nEnter contribution type: ").strip().lower()

    if category not in POINTS:
        print("Invalid contribution category!")
        return

    try:
        count = int(input("Enter number of contributions: "))

        if count <= 0:
            print("Enter a positive number!")
            return

    except ValueError:
        print("Please enter a valid number!")
        return

    participant["contributions"][category] += count

    save_data()

    print("\nContribution added successfully!")


# Generate leaderboard
def generate_leaderboard():

    leaderboard = []

    for participant in participants:

        contributions = participant["contributions"]

        score = calculate_score(contributions)

        total_commits = sum(contributions.values())

        leaderboard.append({
            "name": participant["name"],
            "score": score,
            "commits": total_commits
        })

    leaderboard.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return leaderboard


# Display leaderboard
def display_leaderboard():

    leaderboard = generate_leaderboard()

    print("\n" + "=" * 55)
    print("       OPEN SOURCE CONTRIBUTION LEADERBOARD")
    print("=" * 55)

    print(f"{'RANK':<8}{'NAME':<15}{'COMMITS':<12}{'SCORE'}")

    print("-" * 55)

    for rank, participant in enumerate(leaderboard, start=1):

        print(
            f"{rank:<8}"
            f"{participant['name']:<15}"
            f"{participant['commits']:<12}"
            f"{participant['score']}"
        )

    print("=" * 55)


# Search participant
def search_participant():

    name = input("\nEnter participant name: ").strip()

    participant = next(
        (p for p in participants if p["name"].lower() == name.lower()),
        None
    )

    if participant is None:
        print("Participant not found!")
        return

    contributions = participant["contributions"]

    score = calculate_score(contributions)

    print("\n" + "=" * 40)
    print("       PARTICIPANT DETAILS")
    print("=" * 40)

    print("Name:", participant["name"])

    print("\nContributions:")

    for category, count in contributions.items():
        print(f"{category}: {count}")

    print("\nTotal Score:", score)

    print("=" * 40)


# Main application
def main():

    while True:

        print("\n" + "=" * 45)
        print("       OPEN SOURCE LEADERBOARD")
        print("=" * 45)

        print("1. Add Participant")
        print("2. Add Contribution")
        print("3. View Leaderboard")
        print("4. Search Participant")
        print("5. Exit")

        print("=" * 45)

        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            add_participant()

        elif choice == "2":
            add_contribution()

        elif choice == "3":
            display_leaderboard()

        elif choice == "4":
            search_participant()

        elif choice == "5":
            print("\nThank you for using the application!")
            break

        else:
            print("\nInvalid choice! Please try again.")


if __name__ == "__main__":
    main()