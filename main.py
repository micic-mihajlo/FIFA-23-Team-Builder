import argparse
import pandas as pd
import random
from player import Player
from team import Team

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Build the best FIFA 23 team within a given budget or the greatest squad.')
    parser.add_argument('budget', type=int, nargs='?', default=None, help='The total cost of the team should not exceed this value.')
    parser.add_argument('--formation', type=str, default='4-4-2', help='The formation of the team. Default is "4-4-2".')
    parser.add_argument('--min_chemistry', type=int, default=0, help='The minimum chemistry for the team.')
    parser.add_argument('--greatest_squad', action='store_true', help='If provided, disregards the budget and just creates the greatest squad with players having performance score higher than 98 and chemistry higher than 30.')
    parser.add_argument('--legend_squad', action='store_true', help='Generate a squad with only players with performance scores greater than 97 in their positions.')

    args = parser.parse_args()

    # Map formations to player positions
    formations = {
        '4-4-2': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 2},
        '4-3-3': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 3, 'LW': 1, 'RW': 1, 'ST': 1},
        '3-5-2': {'GK': 1, 'CB': 3, 'LM': 1, 'RM': 1, 'CDM': 2, 'CAM': 1, 'ST': 2},
        '4-2-3-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CDM': 2, 'CAM': 3 ,'ST': 1},
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
    df = pd.read_excel('players_price_update.xlsx')
    players = [Player(row) for index, row in df.iterrows() if row["Cost"] > 15000]

    # Initialize greatest squad flag
    greatest_squad = args.greatest_squad

    #Initialize legend squad flag
    legend_squad = args.legend_squad


    # If greatest squad is to be generated, filter players and set minimum chemistry to 30
    if greatest_squad:
        players = [player for player in players if any(score > 98 for score in player.performance_scores.values())]
        MIN_CHEMISTRY = 29
    else:
        BUDGET = args.budget



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
    
    # Set the minimum score based on whether you are generating the greatest squad or not
    if greatest_squad:
        min_score = 99
    elif legend_squad:
        min_score = 97
    else:
        min_score = 89



    # Generate initial population
    population = []
    while len(population) < POPULATION_SIZE:
        players_list = []
        already_chosen_player_names = []
        for position, count in FORMATION.items():
            if position in data:
                available_players = [player for player in data[position] 
                                    if player.performance_scores[position] > min_score 
                                    and player.name not in already_chosen_player_names]
                chosen_players = random.sample(available_players, k=count)
                for player in chosen_players:
                    player.selected_position = position  # Set selected_position
                    already_chosen_player_names.append(player.name)  # Immediately update chosen players
                players_list.extend(chosen_players)
            else:
                print(f"No players can play the position {position}")
                return
        team = Team(players_list)
        if team.calculate_chemistry() >= MIN_CHEMISTRY:
            population.append(team)




    # Run genetic algorithm
    for generation in range(12500):  # Run for 20000 generations
        if generation % 100 == 0: print(f"Generation {generation}")

        # Calculate fitness values
        fitness_values = [team.fitness(BUDGET, MIN_CHEMISTRY) if team.calculate_chemistry() >= MIN_CHEMISTRY else 1500 for team in population]

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
            already_chosen_player_names = []  # this will hold names of players already added to the team
            for position, count in FORMATION.items():
                parent_choice = random.choice([parent1, parent2])
                parent_players = [player for player in parent_choice.players 
                    if player.selected_position == position 
                    and player.performance_scores[position] > min_score
                    and player.name not in already_chosen_player_names]  # filter out already chosen players

                if len(parent_players) >= count:
                    selected_players = random.sample(parent_players, count)
                    for player in selected_players:
                        already_chosen_player_names.append(player.name)  # add the chosen player's name to the list of already chosen players
                    new_team_players.extend(selected_players)
                else:
                    remaining_needed = count - len(parent_players)
                    additional_players = random.sample([p for p in data[position] 
                                                    if p.name not in already_chosen_player_names  # also here, filter out already chosen players
                                                    and p.performance_scores[position] > min_score], 
                                                remaining_needed)
                    for player in additional_players:
                        already_chosen_player_names.append(player.name)  # add the chosen player's name to the list of already chosen players
                    new_team_players.extend(additional_players)
            new_team = Team(new_team_players)
            if new_team.calculate_chemistry() >= MIN_CHEMISTRY:
                population.append(new_team)







        # Perform mutation
        for i, team in enumerate(population):
            if random.random() < 0.1:
                old_player = random.choice(team.players)
                if old_player.selected_position is None or old_player.selected_position not in data:
                    continue
                team_player_names = set(player.name for player in team.players)  # Convert list to set for faster membership checks
                possible_replacements = [player for player in data[old_player.selected_position] if player != old_player]
                if not greatest_squad:  # If it's not the greatest squad, then consider the budget
                    possible_replacements = [player for player in possible_replacements if player.cost <= old_player.cost]
                unique_replacements = []  # Initialize unique_replacements to an empty list
                if possible_replacements:
                    unique_replacements = [p for p in possible_replacements if p.name not in team_player_names]
                if unique_replacements:
                    new_player = random.choice(unique_replacements)
                    new_player.selected_position = old_player.selected_position  # Set selected_position
                    team.players[team.players.index(old_player)] = new_player
                    population[i] = Team(team.players)  # Convert the updated player list back to a Team object









        # Replace over-budget teams
        if not greatest_squad:  # If it's not greatest squad, then consider budget
            for i, team in enumerate(population):
                while team.cost() > BUDGET:
                    old_player = max(team.players, key=lambda p: p.cost)
                    possible_replacements = [player for player in players if player.cost < old_player.cost and player.cost > 0 and old_player.main_position == player.main_position or old_player.main_position in player.alt_positions]
                    if possible_replacements:
                        new_player = random.choice(possible_replacements)
                        team.players[team.players.index(old_player)] = new_player
                    else:
                        break
        
        # Remove teams with duplicate players
        population = [team for team in population if len(set(player.name for player in team.players)) == len(team.players)]



    # Display best team
    best_team = max(population, key=lambda team: team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY))
    print("\nBest Team:")
    for position in FORMATION:
        players_in_position = [player for player in best_team.players if player.selected_position == position]
        for player in players_in_position:
            print(f"{position}: {player.name} (DA Score: {player.performance_scores[player.selected_position]}, Cost: {player.cost})")
    print(f"Total rating: {round(best_team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY), 2)}, Total cost: {round(best_team.cost(), 2)}, Chemistry: {best_team.calculate_chemistry()} out of 33")




if __name__ == '__main__':
    main()
