class Team:
    def __init__(self, players):
        self.players = players

    def cost(self):
        return sum(player.cost for player in self.players)

    def calculate_chemistry(self):
        total_chemistry = 0
        for player in self.players:
            chem = 0

            # calculate club chemistry
            same_club_count = sum(1 for p in self.players if p.club == player.club)
            if same_club_count >= 7:
                chem += 3
            elif same_club_count >= 4:
                chem += 2
            elif same_club_count >= 2:
                chem += 1

            # calculate nationality chemistry
            same_nationality_count = sum(1 for p in self.players if p.nationality == player.nationality)
            same_nationality_count += sum(2 for p in self.players if p.nationality == player.nationality and "FUT ICONS" in p.club)  # Icons count double
            if same_nationality_count >= 8:
                chem = min(chem + 3, 3)
            elif same_nationality_count >= 5:
                chem = min(chem + 2, 3)
            elif same_nationality_count >= 2:
                chem = min(chem + 1, 3)

            # calculate league chemistry
            same_league_count = sum(1 for p in self.players if p.league == player.league)
            same_league_count += sum(2 for p in self.players if p.league == player.league and "HERO" in p.club)  # Heroes count double
            if same_league_count >= 8:
                chem = min(chem + 3, 3)
            elif same_league_count >= 5:
                chem = min(chem + 2, 3)
            elif same_league_count >= 3:
                chem = min(chem + 1, 3)

            total_chemistry += chem
        return total_chemistry

    def fitness(self, budget):
        performance_score = sum(player.performance_scores[player.selected_position] for player in self.players if player.selected_position in player.performance_scores)
        total_chemistry = self.calculate_chemistry()
        team_cost = self.cost()
        budget_utilization = abs(budget - team_cost)
        return performance_score + total_chemistry * 125 - budget_utilization / 5000

    def meets_min_chemistry(self, min_chemistry):
        return self.calculate_chemistry() >= min_chemistry
