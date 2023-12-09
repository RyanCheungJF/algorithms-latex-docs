import imagematrix


class ResizeableImage(imagematrix.ImageMatrix):
    def best_seam_dp(self):
        # tracks costs for previous row only, since recurrence only depends on it
        costs = [10000] * self.width
        # tracks costs for current row only
        temp = [0] * self.width
        # cache to track energy values to avoid re-computation
        energy = {}

        # dictionary of pointers to track path
        path = {}
        # initialize with base case, first row
        for i in range(self.width):
            path[(i, 0)] = (None, None)

        for j in range(1, self.height):
            for i in range(self.width):
                left = costs[i - 1] if i > 0 else float("inf")
                top = costs[i]
                right = costs[i + 1] if i < self.width - 1 else float("inf")
                lowest_energy = min(left, top, right)
                energy_cost = energy.get((i, j), self.energy(i, j))
                if (i, j) not in energy:
                    energy[(i, j)] = energy_cost
                # write to a temp arr as we still need the other costs value
                temp[i] = lowest_energy + energy_cost

                # path tracking
                # if somehow two paths give the same lowest energy,
                # then just take either as both paths are minimum
                if lowest_energy == left:
                    prev = (i - 1, j - 1)
                elif lowest_energy == top:
                    prev = (i, j - 1)
                else:
                    prev = (i + 1, j - 1)
                path[(i, j)] = prev

            # replace costs with new set of minimum values calculated
            # copy to prevent python copy by reference
            costs = temp[:]

        # find minimum cost for last row, and coordinates to start backtracking
        res, index = float("inf"), -1
        for i, val in enumerate(costs):
            if val < res:
                res, index = val, i

        # trace path
        x, y = index, self.height - 1
        seam = []
        while x is not None and y is not None:
            seam.append((x, y))
            x, y = path.get((x, y))

        return seam
        

    def best_seam_naive(self):
        energy = {}

        def dfs(i, j, path):
            if i < 0 or i >= self.width or j < 0 or j >= self.height:
                return float("inf"), path
            # recurrence is for rows only, so base case is very first row having fixed cost
            if j == 0:
                return 10000, path

            # recurrence
            # trade off for more space for less time
            # we use more space for copies of lists,
            # but doesn't require another backtracking step just like in dp
            left, left_path = dfs(i - 1, j - 1, path[:])
            top, top_path = dfs(i, j - 1, path[:])
            right, right_path = dfs(i + 1, j - 1, path[:])
            lowest_energy = min(left, top, right)
            
            energy_cost = self.energy(i, j)
            energy_cost = energy.get((i, j), self.energy(i, j))
            if (i, j) not in energy:
                energy[(i, j)] = energy_cost

            # path tracking
            if lowest_energy == left:
                left_path.append((i - 1, j - 1))
                return lowest_energy + energy_cost, left_path
            elif lowest_energy == top:
                top_path.append((i, j - 1))
                return lowest_energy + energy_cost, top_path
            else:
                right_path.append((i + 1, j - 1))
                return lowest_energy + energy_cost, right_path

        res = float("inf")
        seam = []
        for i in range(self.width):
            path = [(i, self.height - 1)]
            cost, coordinates = dfs(i, self.height - 1, path)
            if cost < res:
                res = cost
                seam = coordinates

        return seam

    def best_seam(self, dp=True):
        return self.best_seam_dp() if dp else self.best_seam_naive()

    def remove_best_seam(self):
        self.remove_seam(self.best_seam())
