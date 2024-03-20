import streamlit as st
import argparse
import pandas as pd
import random
from player import Player
from team import Team
import collections
import sys

st.title("FIFA 23 Ultimate Team Squad Generator")


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

budget = st.slider("Budget", min_value=1000000, max_value=10000000, value=5000000, step=100000)
formation = st.selectbox("Formation", list(formations.keys()), index=list(formations.keys()).index('4-4-2'))
min_chemistry = st.slider("Minimum Chemistry", min_value=0, max_value=33, value=27)
greatest_squad = st.checkbox("Generate Greatest Squad", help="Generates the squad with the highest total rating and no matter the cost.")
legend_squad = st.checkbox("Generate Legend Squad")
specific_players = st.text_input("Specific Players (DAId:position pairs, separated by spaces)")


POPULATION_SIZE = 100
BUDGET = budget
FORMATION = formations[formation]
MIN_CHEMISTRY = min_chemistry
if MIN_CHEMISTRY < 0 or MIN_CHEMISTRY > 33:
    raise ValueError("Minimum chemistry must be between 0 and 33 inclusive.")

specific_players_info = {int(player.split(':')[0]): player.split(':')[1] for player in specific_players.split()} if specific_players else {}

df = pd.read_excel('players_price_update.xlsx')
players = [Player(row) for index, row in df.iterrows() if row["Cost"] > 15000]

specific_players = {player.DAId: player for player in players if player.DAId in specific_players_info.keys()}
players = [player for player in players if player.DAId not in specific_players_info.keys()]

specific_players_cost = sum(player.cost for player in specific_players.values())

if greatest_squad:
    players = [player for player in players if any(score > 98 for score in player.performance_scores.values())]
    MIN_CHEMISTRY = 29
else:
    BUDGET = budget

all_positions = set()
for player in players:
    all_positions.add(player.main_position)
    all_positions.update(player.alt_positions)

data = {position: [] for position in all_positions}

for player in players:
    for position in [player.main_position] + list(player.alt_positions):
        data[position].append(player)

if greatest_squad:
    min_score = 98.75
elif legend_squad:
    min_score = 97
else:
    min_score = 89

population = []
while len(population) < POPULATION_SIZE:
    players_list = []
    already_chosen_player_names = []

    for DAId, player in specific_players.items():
        player.selected_position = specific_players_info[DAId]
        already_chosen_player_names.append(player.name)
        players_list.append(player)

    for position, count in FORMATION.items():
        if position in data:
            available_players = [player for player in data[position] 
                                if player.performance_scores[position] > min_score 
                                and player.name not in already_chosen_player_names]
            chosen_players = random.sample(available_players, k=count)
            for player in chosen_players:
                player.selected_position = position
                already_chosen_player_names.append(player.name)
            players_list.extend(chosen_players)
        else:
            print(f"No players can play the position {position}")
            sys.exit()
    team = Team(players_list)
    if team.calculate_chemistry() >= MIN_CHEMISTRY:
        population.append(team)
loading_message_placeholder = st.empty()
progress_bar_placeholder = st.empty()
if st.button("Generate Squad"):
    loading_message_placeholder.text("Generating the ultimate squad... ⚽🌟")
    progress_bar = progress_bar_placeholder.progress(0)
    for generation in range(1500):
        progress_bar.progress((generation + 1) / 1500)

        if generation % 100 == 0: print(f"Generation {generation}")

        fitness_values = [team.fitness(BUDGET, MIN_CHEMISTRY, specific_players_cost) if team.calculate_chemistry() >= MIN_CHEMISTRY else 1500 for team in population]

        parents = []
        while len(parents) < POPULATION_SIZE:
            parent = random.choices(population, weights=fitness_values, k=1)[0]
            if parent.calculate_chemistry() >= MIN_CHEMISTRY:
                parents.append(parent)

        population = []
        for parent1, parent2 in zip(parents[::2], parents[1::2]):
            new_team_players = []
            already_chosen_positions = collections.defaultdict(int)
            new_team_players.extend(specific_players.values())
            for player in specific_players.values():
                already_chosen_positions[player.selected_position] += 1
            for position, count in FORMATION.items():
                if already_chosen_positions[position] >= count:
                    continue
                parent_choice = random.choice([parent1, parent2])
                parent_players = [player for player in parent_choice.players 
                    if player.selected_position == position 
                    and player.performance_scores[position] > min_score
                    and player.DAId not in specific_players.keys()]

                selected_players = random.sample(parent_players, min(count - already_chosen_positions[position], len(parent_players)))

                for player in selected_players:
                    already_chosen_positions[player.selected_position] += 1
                new_team_players.extend(selected_players)

                if already_chosen_positions[position] < count:
                    remaining_needed = count - already_chosen_positions[position]
                    additional_players = [p for p in data[position] 
                                        if p.DAId not in specific_players.keys()
                                        and p.performance_scores[position] > min_score
                                        and already_chosen_positions[p.selected_position] < count]

                    additional_players = random.sample(additional_players, min(remaining_needed, len(additional_players)))

                    for player in additional_players:
                        already_chosen_positions[player.selected_position] += 1
                    new_team_players.extend(additional_players)
            new_team = Team(new_team_players)
            if new_team.calculate_chemistry() >= MIN_CHEMISTRY:
                population.append(new_team)

        for i, team in enumerate(population):
            if random.random() < 0.1:
                old_player = random.choice([player for player in team.players if player.DAId not in specific_players.keys()])
                if old_player.selected_position is None or old_player.selected_position not in data:
                    continue

                possible_replacements = [player for player in data[old_player.selected_position] if player != old_player and player.DAId not in specific_players.keys()]

                if not greatest_squad:
                    possible_replacements = [player for player in possible_replacements if player.cost <= old_player.cost]

                possible_replacements.sort(key=lambda p: p.performance_scores[old_player.selected_position], reverse=True)

                for new_player in possible_replacements:
                    new_team_players = [new_player if player == old_player else player for player in team.players]
                    new_team = Team(new_team_players)

                    if new_team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY, specific_players_cost) > team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY, specific_players_cost) and new_team.calculate_chemistry() >= MIN_CHEMISTRY:
                        population[i] = new_team
                        break

        if not greatest_squad:
            for i, team in enumerate(population):
                while team.cost() > BUDGET:
                    expensive_players = [player for player in team.players if player.DAId not in specific_players.keys()]
                    if not expensive_players: 
                        break

                    old_player = max(expensive_players, key=lambda p: p.cost) 

                    possible_replacements = [player for player in players 
                                            if player.cost < old_player.cost and player.cost > 0 
                                            and (old_player.main_position == player.main_position or old_player.main_position in player.alt_positions)]
                    if possible_replacements:
                        new_player = random.choice(possible_replacements)
                        team.players[team.players.index(old_player)] = new_player
                    else:
                        break

        population = [team for team in population if len(set(player.name for player in team.players)) == len(team.players)]
    loading_message_placeholder.empty()
    progress_bar_placeholder.empty()
    best_team = max(population, key=lambda team: team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY+2, specific_players_cost))
    st.subheader("Best Team:")
    for position in FORMATION:
        players_in_position = [player for player in best_team.players if player.selected_position == position]
        for player in players_in_position:
            st.write(f"{position}: {player.name} (DA Score: {player.performance_scores[player.selected_position]}, Cost: {player.cost})")
    st.write(f"Total rating: {round(best_team.fitness(None if greatest_squad else BUDGET, MIN_CHEMISTRY), 2)}, Total cost: {round(best_team.cost(), 2)}, Chemistry: {best_team.calculate_chemistry()} out of 33")
