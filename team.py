from collections import Counter

class Team:
    def __init__(self, players):
        self.players = players
        self.club_counts = Counter(player.club for player in self.players)
        self.nationality_counts = Counter(player.nationality for player in self.players)
        self.league_counts = Counter(player.league for player in self.players)
        self.chemistry = None  # This will be used to store the chemistry once calculated

    def cost(self):
        return sum(player.cost for player in self.players)

    def calculate_chemistry(self):
        # If chemistry was already calculated, return it
        if self.chemistry is not None:
            return self.chemistry

        total_chemistry = 0
        for player in self.players:
            chem = 0

            # calculate club chemistry
            same_club_count = self.club_counts[player.club]
            if same_club_count >= 7:
                chem += 3
            elif same_club_count >= 4:
                chem += 2
            elif same_club_count >= 2:
                chem += 1

            # calculate nationality chemistry
            same_nationality_count = self.nationality_counts[player.nationality]
            same_nationality_count += sum(2 for p in self.players if p.nationality == player.nationality and "FUT ICONS" in p.club)  # Icons count double
            if same_nationality_count >= 8:
                chem = min(chem + 3, 3)
            elif same_nationality_count >= 5:
                chem = min(chem + 2, 3)
            elif same_nationality_count >= 2:
                chem = min(chem + 1, 3)

            # calculate league chemistry
            same_league_count = self.league_counts[player.league]
            same_league_count += sum(2 for p in self.players if p.league == player.league and "HERO" in p.club)  # Heroes count double
            if same_league_count >= 8:
                chem = min(chem + 3, 3)
            elif same_league_count >= 5:
                chem = min(chem + 2, 3)
            elif same_league_count >= 3:
                chem = min(chem + 1, 3)

            total_chemistry += chem

        # Store the calculated chemistry for future use
        self.chemistry = total_chemistry

        return total_chemistry

    def fitness(self, budget, min_chemistry, specific_players_cost=0):
        total_chemistry = self.calculate_chemistry()
        if total_chemistry < min_chemistry:
            return 0
        performance_score = sum(player.performance_scores.get(player.selected_position, 0) for player in self.players)
        team_cost = self.cost() - specific_players_cost
        budget_utilization = abs(budget - team_cost) if budget is not None else 0  # Ignore budget if None
        return performance_score * 30 + total_chemistry * 225 - budget_utilization / 10000

