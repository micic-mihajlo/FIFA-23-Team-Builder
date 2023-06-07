import argparse
import pandas as pd
import random
from player import Player
from team import Team

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Build the best FIFA 23 team within a given budget.')
    parser.add_argument('budget', type=int, help='The total cost of the team should not exceed this value.')
    parser.add_argument('--formation', type=str, default='4-4-2', help='The formation of the team. Default is "4-4-2".')
    parser.add_argument('--min_chemistry', type=int, default=0, help='The minimum chemistry for the team.')
    args = parser.parse_args()

    # Map formations to player positions
    formations = {
        '4-4-2': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 2},
        '4-3-3': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 3, 'LW': 1, 'RW': 1, 'ST': 1},
        '3-5-2': {'GK': 1, 'CB': 3, 'LM': 1, 'RM': 1, 'CDM': 2, 'CAM': 1, 'ST': 2},
        '4-2-3-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CDM': 2, 'CAM': 1, 'LM': 1, 'RM': 1, 'ST': 1},
        '4-5-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 1, 'CDM': 2, 'LM': 1, 'RM': 1, 'ST': 1},
        '4-1-4-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CDM': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 1},
        '5-3-2': {'GK': 1, 'CB': 3, 'LB': 1, 'RB': 1, 'CM': 3, 'ST': 2},
        '5-4-1': {'GK': 1, 'CB': 3, 'LB': 1, 'RB': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 1},
    }

    if args.formation not in formations:
        print(f'Error: Invalid formation "{args.formation}". Available formations are: {", ".join(formations.keys())}')
        return

    # Set constants
    POPULATION_SIZE = 100
    BUDGET = args.budget
    FORMATION = formations[args.formation]
    MIN_CHEMISTRY = args.min_chemistry
    if MIN_CHEMISTRY < 0 or MIN_CHEMISTRY > 33:
        raise ValueError("Minimum chemistry must be between 0 and 33 inclusive.")

    # Load data and initialize as before...
    # Remember to replace the file path with your own
    df = pd.read_excel('player_fulltable.xlsx')
    players = [Player(row) for index, row in df.iterrows() if row["Cost"] > 19000]

    # Collect all possible positions
    all_positions = set()
    for player in players:
        all_positions.add(player.main_position)
        all_positions.update(player.alt_positions)
    
    # Initialize data dictionary
    data = {position: [] for position in all_positions}

    # Add each player to each position they can play in
    for player in players:
        for position in [player.main_position] + list(player.alt_positions):
            data[position].append(player)
    
    # Generate initial population
    population = []
    while len(population) < POPULATION_SIZE:
        team = []
        for position, count in FORMATION.items():
            # Check if the position exists in the 'data' dictionary before proceeding
            if position in data:
                chosen_players = random.choices(data[position], k=count)
                for player in chosen_players:
                    player.selected_position = position  # Set selected_position
                team.extend(chosen_players)
            else:
                print(f"No players can play the position {position}")
                return
        team = Team(team)
        if team.calculate_chemistry() >= MIN_CHEMISTRY:
            population.append(team)



    # Run genetic algorithm
    for generation in range(10000):  # Run for 20000 generations
        print(f"Generation {generation}")

        # Calculate fitness values
        fitness_values = [team.fitness(BUDGET, MIN_CHEMISTRY) if team.calculate_chemistry() >= MIN_CHEMISTRY else 100 for team in population]




        # Select parents
        parents = []
        while len(parents) < POPULATION_SIZE:
            parent = random.choices(population, weights=fitness_values, k=1)[0]
            if parent.calculate_chemistry() >= MIN_CHEMISTRY:
                parents.append(parent)


        # Perform crossover
        population = []
        for parent1, parent2 in zip(parents[::2], parents[1::2]):
            new_team_players = []
            for position, count in FORMATION.items():
                parent1_players = [player for player in parent1.players if player.selected_position == position]
                parent2_players = [player for player in parent2.players if player.selected_position == position]
                unique_parents = list(set(parent1_players + parent2_players))
                if len(unique_parents) >= count:
                    selected_players = random.sample(unique_parents, count)
                    for player in selected_players:
                        player.selected_position = position  # Set selected_position
                else:
                    remaining_needed = count - len(unique_parents)
                    additional_players = random.sample([p for p in data[position] if p not in unique_parents], remaining_needed)
                    for player in additional_players:
                        player.selected_position = position  # Set selected_position
                    selected_players = unique_parents + additional_players
                new_team_players.extend(selected_players)
            new_team = Team(new_team_players)
            if new_team.calculate_chemistry() >= MIN_CHEMISTRY:
                population.append(new_team)


        # Perform mutation
        for team in population:
            if random.random() < 0.1:  # 20% mutation rate
                old_player = random.choice(team.players)
                possible_replacements = [player for player in data[old_player.selected_position] if player.cost < old_player.cost and player != old_player]
                unique_replacements = [p for p in possible_replacements if p.name not in [player.name for player in team.players]]
                if unique_replacements:
                    new_player = random.choice(unique_replacements)
                    new_player.selected_position = old_player.selected_position  # Set selected_position
                    team.players[team.players.index(old_player)] = new_player


        # Replace over-budget teams
        for i, team in enumerate(population):
            while team.cost() > BUDGET:
                old_player = max(team.players, key=lambda p: p.cost)
                possible_replacements = [player for player in players if player.cost < old_player.cost and player.cost > 0 and old_player.main_position == player.main_position or old_player.main_position in player.alt_positions]
                if possible_replacements:
                    new_player = random.choice(possible_replacements)
                    team.players[team.players.index(old_player)] = new_player
                else:
                    break



    # Display best team
    best_team = max(population, key=lambda team: team.fitness(BUDGET, MIN_CHEMISTRY))


    print("\nBest Team:")
    for position in FORMATION:
        players_in_position = [player for player in best_team.players if player.selected_position == position]
        for player in players_in_position:
            print(f"{position}: {player.name} (DA Score: {player.performance_scores[player.selected_position]}, Cost: {player.cost})")
    print(f"Total rating: {round(best_team.fitness(BUDGET, MIN_CHEMISTRY), 2)}, Total cost: {round(best_team.cost(), 2)}, Chemistry: {best_team.calculate_chemistry()} out of 33")


if __name__ == '__main__':
    main()
