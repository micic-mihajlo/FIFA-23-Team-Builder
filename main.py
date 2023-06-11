import argparse
import pandas as pd
import random
from player import Player
from team import Team
import collections

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Build the best FIFA 23 team within a given budget or the greatest squad.')
    parser.add_argument('budget', type=int, nargs='?', default=None, help='The total cost of the team should not exceed this value.')
    parser.add_argument('--formation', type=str, default='4-4-2', help='The formation of the team. Default is "4-4-2".')
    parser.add_argument('--min_chemistry', type=int, default=0, help='The minimum chemistry for the team.')
    parser.add_argument('--greatest_squad', action='store_true', help='If provided, disregards the budget and just creates the greatest squad with players having performance score higher than 98 and chemistry higher than 30.')
    parser.add_argument('--legend_squad', action='store_true', help='Generate a squad with only players with performance scores greater than 97 in their positions.')
    parser.add_argument('--specific_players', nargs='+', type=str, help='DAIds of specific players that must be included in the team. Should be passed as DAId:position pairs (e.g. 415:CM 237:ST).')


    args = parser.parse_args()

    # Map formations to player positions
    formations = {
        '4-4-2': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 2},
        '4-2-4': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'LW': 1, 'CM': 2, 'RW': 1, 'ST': 2},
        '4-3-3': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 3, 'LW': 1, 'RW': 1, 'ST': 1},
        '3-5-2': {'GK': 1, 'CB': 3, 'LM': 1, 'RM': 1, 'CDM': 2, 'CAM': 1, 'ST': 2},
        '4-2-3-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CDM': 2, 'CAM': 3 ,'ST': 1},
        '4-5-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 1, 'CDM': 2, 'LM': 1, 'RM': 1, 'ST': 1},
        '4-1-4-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CDM': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 1},
        '5-3-2': {'GK': 1, 'CB': 3, 'LB': 1, 'RB': 1, 'CM': 3, 'ST': 2},
        '5-4-1': {'GK': 1, 'CB': 3, 'LB': 1, 'RB': 1, 'LM': 1, 'CM': 2, 'RM': 1, 'ST': 1},
        '4-3-2-1': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 3, 'CF': 2, 'ST': 1},
        '4-3-3_4': {'GK': 1, 'CB': 2, 'LB': 1, 'RB': 1, 'CM': 2, 'CAM': 1, 'LW': 1, 'RW': 1, 'ST': 1},
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
    

    # Process specific players argument
    specific_players_info = {int(player.split(':')[0]): player.split(':')[1] for player in args.specific_players} if args.specific_players else {}


    # Load data and initialize as before...
    df = pd.read_excel('players_price_update.xlsx')
    players = [Player(row) for index, row in df.iterrows() if row["Cost"] > 15000]

    # Split specific players from the general pool of players
    specific_players = {player.DAId: player for player in players if player.DAId in specific_players_info.keys()}
    players = [player for player in players if player.DAId not in specific_players_info.keys()]

    specific_players_cost = sum(player.cost for player in specific_players.values())


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
        min_score = 98.75
    elif legend_squad:
        min_score = 97
    else:
        min_score = 89
    

    # Generate initial population
    population = []
    while len(population) < POPULATION_SIZE:
        players_list = []
        already_chosen_player_names = []

        # First add specific players to the team and the list of already chosen players
        for DAId, player in specific_players.items():
            player.selected_position = specific_players_info[DAId]  # Set selected_position to the provided position
            already_chosen_player_names.append(player.name)  # Immediately update chosen players
            players_list.append(player)

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
    for generation in range(7500):  # Run for 20000 generations
        if generation % 100 == 0: print(f"Generation {generation}")

        # Calculate fitness values
        fitness_values = [team.fitness(BUDGET, MIN_CHEMISTRY, specific_players_cost) if team.calculate_chemistry() >= MIN_CHEMISTRY else 1500 for team in population]


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
            already_chosen_positions = collections.defaultdict(int)  # Change to a dict to keep track of counts
            # add specific players to the new team players
            new_team_players.extend(specific_players.values())
            for player in specific_players.values():
                already_chosen_positions[player.selected_position] += 1
            for position, count in FORMATION.items():
                if already_chosen_positions[position] >= count:  # if enough players of position already filled, continue to next
                    continue
                parent_choice = random.choice([parent1, parent2])
                parent_players = [player for player in parent_choice.players 
                    if player.selected_position == position 
                    and player.performance_scores[position] > min_score
                    and player.DAId not in specific_players.keys()]  # Exclude specific players

                # Modified part: choose min between available players and needed players
                selected_players = random.sample(parent_players, min(count - already_chosen_positions[position], len(parent_players)))

                for player in selected_players:
                    already_chosen_positions[player.selected_position] += 1
                new_team_players.extend(selected_players)

                # If there are still spots left for the position, select additional players
                if already_chosen_positions[position] < count:
                    remaining_needed = count - already_chosen_positions[position]
                    additional_players = [p for p in data[position] 
                                        if p.DAId not in specific_players.keys()  # Exclude specific players
                                        and p.performance_scores[position] > min_score
                                        and already_chosen_positions[p.selected_position] < count]  # only select if less than required players have been chosen

                    # Choose the smaller between remaining_needed and available players
                    additional_players = random.sample(additional_players, min(remaining_needed, len(additional_players)))

                    for player in additional_players:
                        already_chosen_positions[player.selected_position] += 1
                    new_team_players.extend(additional_players)
            new_team = Team(new_team_players)
            if new_team.calculate_chemistry() >= MIN_CHEMISTRY:
                population.append(new_team)




        # Perform mutation
        for i, team in enumerate(population):
            if random.random() < 0.1:  # 10% mutation rate
                old_player = random.choice([player for player in team.players if player.DAId not in specific_players.keys()])  # Exclude specific players
                if old_player.selected_position is None or old_player.selected_position not in data:
                    continue

                # Get a list of possible replacements
                possible_replacements = [player for player in data[old_player.selected_position] if player != old_player and player.DAId not in specific_players.keys()]  # Exclude specific players

                # If we're not generating the greatest squad, consider the budget
                if not greatest_squad:
                    possible_replacements = [player for player in possible_replacements if player.cost <= old_player.cost]

                # Prioritize players who can enhance the overall team's score
                possible_replacements.sort(key=lambda p: p.performance_scores[old_player.selected_position], reverse=True)

                for new_player in possible_replacements:
                    new_team_players = [new_player if player == old_player else player for player in team.players]
                    new_team = Team(new_team_players)  # Generate a new team with the proposed player swap

                    # If the new team is better than the old team, make the swap
                    if new_team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY, specific_players_cost) > team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY, specific_players_cost) and new_team.calculate_chemistry() >= MIN_CHEMISTRY:
                        population[i] = new_team
                        break  # Once a suitable replacement has been found, break the loop



        # Replace over-budget teams
        if not greatest_squad:  # If it's not greatest squad, then consider budget
            for i, team in enumerate(population):
                while team.cost() > BUDGET:
                    # Filter players that are not in the specific_players list and get the most expensive one
                    expensive_players = [player for player in team.players if player.DAId not in specific_players.keys()]
                    if not expensive_players: 
                        break

                    old_player = max(expensive_players, key=lambda p: p.cost) 

                    # Filter possible replacements: cheaper, positive cost, and compatible position
                    possible_replacements = [player for player in players 
                                            if player.cost < old_player.cost and player.cost > 0 
                                            and (old_player.main_position == player.main_position or old_player.main_position in player.alt_positions)]
                    if possible_replacements:
                        new_player = random.choice(possible_replacements)
                        team.players[team.players.index(old_player)] = new_player
                    else:
                        break

        
        # Remove teams with duplicate players
        population = [team for team in population if len(set(player.name for player in team.players)) == len(team.players)]



    # Display best team
    best_team = max(population, key=lambda team: team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY+2, specific_players_cost))
    print("\nBest Team:")
    for position in FORMATION:
        players_in_position = [player for player in best_team.players if player.selected_position == position]
        for player in players_in_position:
            print(f"{position}: {player.name} (DA Score: {player.performance_scores[player.selected_position]}, Cost: {player.cost})")
    print(f"Total rating: {round(best_team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY), 2)}, Total cost: {round(best_team.cost(), 2)}, Chemistry: {best_team.calculate_chemistry()} out of 33")




if __name__ == '__main__':
    main()
