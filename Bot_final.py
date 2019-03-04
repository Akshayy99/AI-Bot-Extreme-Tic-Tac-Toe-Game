import sys
import random
import signal
from time import time
import copy
import traceback
from operator import itemgetter

class Team3():

    def __init__(self):
        self.my_player = 1
        self.pl_symbol = ['o', 'x']
        self.bonus_flag = 0
        self.MAX = 1000000000
        self.num_cost = [0,1000,100000,10000000]
        self.bl_pos = [[3,2,3], [2,4,2], [3,2,3]]
        self.first_move = 1
        self.last_small_board_won = 0
        self.transp_table = {}
        self.moves_available = []
        self.small_board_zobrist = ([],[])
        self.small_board_hash = ([],[])
        self.t_start = 0
        self.t_end = 20
        for k in xrange(2):
            for _ in xrange(3):
                self.small_board_hash[k].append([0]*3)
        for k in xrange(2):
            for i in xrange(32):
                self.small_board_zobrist[k].append(2**i)
        self.pos_fac = 1
        self.neg_fac = 1


    
    
    def move(self, board, prev_move, flag):
        
        level = 2
        self.board_hash(board)

        self.my_player = (0,1)[flag == 'x']
        self.bonus_flag = [0, 0]

        player = self.my_player
        self.moves_available = board.find_valid_move_cells(prev_move)
        prev_ans = random.choice(self.moves_available)
        

        if self.last_small_board_won:
            self.bonus_flag[self.my_player] = 1
        
        self.timeup = 0
        self.t_start = time()



        
        if self.first_move == 1:
            self.first_move = 0
            if (0,4,4) in self.moves_available:
                return (0,4,4)
            else:
                return prev_ans
        while self.timeup == 0:

            self.board_hash(board)
            ans = self.best_move_minimax(board,player,prev_move, level)

            if self.timeup == 1:
                break
            prev_ans = ans
            level += 1

        _, small_board_won = self.update(board, prev_move, prev_ans, self.pl_symbol[player])

        if small_board_won:
            if self.last_small_board_won == 0:
                self.last_small_board_won = 1
            elif self.last_small_board_won == 1:
                self.last_small_board_won = 0
        else:
            self.last_small_board_won = 0
        
        board.big_boards_status[prev_ans[0]][prev_ans[1]][prev_ans[2]] = "-"
        board.small_boards_status[prev_ans[0]][prev_ans[1]/3][prev_ans[2]/3] = "-"

        return prev_ans

        
    def update(self, board, prev_move, new_move, ply):
        board.big_boards_status[new_move[0]][new_move[1]][new_move[2]] = ply
        
        x = new_move[1]/3
        y = new_move[2]/3
        k = new_move[0]
        bs = board.big_boards_status[k]
        for i in xrange(3):
            if (bs[3*x+i][3*y] == bs[3*x+i][3*y+1] == bs[3*x+i][3*y+2]) and (bs[3*x+i][3*y] == ply):
                board.small_boards_status[k][x][y] = ply
                return 'SUCCESSFUL', True
            if (bs[3*x][3*y+i] == bs[3*x+1][3*y+i] == bs[3*x+2][3*y+i]) and (bs[3*x][3*y+i] == ply):
                board.small_boards_status[k][x][y] = ply
                return 'SUCCESSFUL', True
        if (bs[3*x][3*y] == bs[3*x+1][3*y+1] == bs[3*x+2][3*y+2]) and (bs[3*x][3*y] == ply):
            board.small_boards_status[k][x][y] = ply
            return 'SUCCESSFUL', True
        if (bs[3*x][3*y+2] == bs[3*x+1][3*y+1] == bs[3*x+2][3*y]) and (bs[3*x][3*y+2] == ply):
            board.small_boards_status[k][x][y] = ply
            return 'SUCCESSFUL', True
        for i in xrange(3):
            for j in xrange(3):
                if bs[3*x+i][3*y+j] =='-':
                    return 'SUCCESSFUL', False
        board.small_boards_status[k][x][y] = 'd'
        return 'SUCCESSFUL', False


    def best_move_minimax(self, board, player, prev_move,level):

        maxval = -self.MAX
        self.moves_available = board.find_valid_move_cells(prev_move)
        bl_won = self.bonus_flag[player]
        best_move = random.choice(self.moves_available)

        for move in self.moves_available:
            self.bonus_flag[player] = bl_won
            
            x = 3*(move[1]%3) + (move[2]%3)
            self.small_board_hash[move[0]][move[1]/3][move[2]/3] ^= (self.small_board_zobrist[move[0]][2*x], self.small_board_zobrist[move[0]][2*x+1]) [player == self.my_player^1]


            _, small_board_won = self.update(board, prev_move, move, self.pl_symbol[player])
            if small_board_won:
                self.bonus_flag[player] = (1, 0)[self.bonus_flag[player]==1]
            else:
                self.bonus_flag[player] = 0
            
            
            if small_board_won and self.bonus_flag[player] == 1:
                score = self.minimax(board, player, player, level-1, move, -self.MAX, self.MAX)
                self.bonus_flag[player] = 0
            else:
                score = self.minimax(board, player^1, player, level-1, move, -self.MAX, self.MAX)
           
            b_no = move[0]
            r_no = move[1]
            c_no = move[2]

            x = 3*(r_no%3) + (c_no%3)
            self.small_board_hash[b_no][r_no/3][c_no/3] ^= (self.small_board_zobrist[b_no][2*x], self.small_board_zobrist[b_no][2*x+1]) [player == self.my_player^1]

            board.small_boards_status[b_no][r_no/3][c_no/3] = "-"
            board.big_boards_status[b_no][r_no][c_no] = "-"


            best_move = (best_move,move)[score > maxval]
            maxval = max(score,maxval)

        self.bonus_flag[player] = bl_won

        return best_move

    def prox(self,move,board,player):

        r_start = int(move[1]/3)*3
        r_end = r_start + 2

        c_start = int(move[2]/3)*3
        c_end = c_start + 2

        dirx = [-1,-1,-1,0,0,0,1,1,1]
        diry = [-1,0,1,-1,0,1,-1,0,1]
        val = 0
        for i in range(9):
            for j in range(9):
                prox_x = move[1] + dirx[i]
                prox_y = move[2] + diry[j]
                if dirx[i] !=0 and diry[i] != 0:
                    if prox_x >= r_start and prox_x <= r_end and prox_y >= c_start and prox_y <= c_end:
                        return 100000
        
        return val

    def minimax(self,board, player, prev_player, level, prev_move, alpha, beta):
        
        if level == 0 or board.find_terminal_state() != ('CONTINUE', '-'):
            return self.heuristic(board, prev_player,prev_move)
        
        if time()-self.t_start >= self.t_end or self.timeup == 1:
            self.timeup = 1
            return self.heuristic(board, prev_player, prev_move)

        possible_moves = board.find_valid_move_cells(prev_move)

        score = (self.MAX, -self.MAX)[self.my_player == player]

        bl_won = self.bonus_flag[player]

        for move in possible_moves:
            self.bonus_flag[player] = bl_won

            x = 3*(move[1]%3) + (move[2]%3)
            self.small_board_hash[move[0]][move[1]/3][move[2]/3] ^= (self.small_board_zobrist[move[0]][2*x], self.small_board_zobrist[move[0]][2*x+1]) [player == self.my_player^1]
            
            _, small_board_won = self.update(board, prev_move, move, self.pl_symbol[player])
            
            if small_board_won:
                self.bonus_flag[player] = (1, 0)[self.bonus_flag[player]==1]
            else:
                self.bonus_flag[player] = 0
            
            if not player == self.my_player:
                if small_board_won and self.bonus_flag[player] == 1:
                    score = min(score, self.minimax(board, player, player, level-1, move, alpha, beta)+self.prox(move,board,player))
                    self.bonus_flag[player] = 0
                else:
                    score = min(score, self.minimax(board, player^1, player, level-1, move, alpha, beta)+self.prox(move,board,player))
                    
                beta = min(beta, score)
            elif player == self.my_player:
                if small_board_won and self.bonus_flag[player] == 1:
                    score = max(score, self.minimax(board, player, player, level-1, move, alpha, beta)+self.prox(move,board,player))
                else:
                    score = max(score, self.minimax(board, player^1, player, level-1, move, alpha, beta)+self.prox(move,board,player))

                alpha = max(alpha, score)

            b_no = move[0]
            r_no = move[1]
            c_no = move[2]

            x = 3*(r_no%3) + (c_no%3)
            self.small_board_hash[b_no][r_no/3][c_no/3] ^= (self.small_board_zobrist[b_no][2*x], self.small_board_zobrist[b_no][2*x+1]) [player == self.my_player^1]

            board.small_boards_status[b_no][r_no/3][c_no/3] = "-"
            board.big_boards_status[b_no][r_no][c_no] = "-"

            if alpha >= beta or self.timeup == 1:
                break;

        self.bonus_flag[player] = bl_won
        return score

    def heuristic(self, board, player, prev_move):
        
        # b_no = old_move[0]

        cur_state = board.find_terminal_state()
        if cur_state[1] == "WON":

            if player == self.my_player:
                return self.MAX
            else:
                return -self.MAX

        cost = [[],[]]
        for k in range(2):
            for i in range(3):
                cost[k].append([0]*3)

        for k in range(2):
            for i in range(3):
                for j in range(3):
                    if(board.small_boards_status[k][i][j] == self.pl_symbol[self.my_player]):
                        cost[k][i][j] += self.pos_fac*self.MAX/100
                    elif(board.small_boards_status[k][i][j] == self.pl_symbol[self.my_player^1]):
                        cost[k][i][j] -= self.neg_fac*self.MAX/100
                    else:
                        if self.small_board_hash[k][i][j] in self.transp_table:
                            cost[k][i][j] = self.transp_table[self.small_board_hash[k][i][j]]
                            if len(self.transp_table) > 8000 :
                                self.transp_table = {}
                        else:
                            temp = self.find_smallboard_cost(board,self.my_player,i,j,k)
                            cost[k][i][j] = temp
                            self.transp_table[self.small_board_hash[k][i][j]] = temp  


        return self.find_bigboard_cost(board,self.my_player,cost)

    def find_bigboard_cost(self, board, player, cost):
        
        row = [[], []]
        col = [[], []]
        diag = [[[], []] ,[[], []]]
        
        col_tot = [[0]*3, [0]*3]
        row_tot = [[0]*3, [0]*3]
        diag_tot =[[0]*2, [0]*2]
        
        for k in range(2):
            for i in range(3):
                row[k].append([])
                col[k].append([])
            
        fac = 1000
        total = 0
        for k in range(2):
            for i in range(3):
                for j in range(3):
                    row[k][i].append(board.small_boards_status[k][i][j])
                    row_tot[k][i] += cost[k][i][j]
        for k in range(2):
            for i in range(3):
                for j in range(3):
                    col[k][j].append(board.small_boards_status[k][j][i])
                    col_tot[k][j] += cost[k][j][i]

        for k in range(2):
            diag[k][0].append(row[k][0][0])
            diag[k][0].append(row[k][1][1])
            diag[k][0].append(row[k][2][2])
            diag_tot[k][0] = cost[k][0][0] + cost[k][1][1] + cost[k][2][2]
            diag[k][1].append(row[k][0][2])
            diag[k][1].append(row[k][1][1])
            diag[k][1].append(row[k][2][0])
            diag_tot[k][1] = cost[k][0][2] + cost[k][1][1] + cost[k][2][0]

        for k in range(2):
            for i in range(3):
                for j in range(3):
                    if row[k][i][j] == self.pl_symbol[self.my_player]:
                        total += self.pos_fac*(self.bl_pos[i][j]*fac)
                    elif row[k][i][j] == self.pl_symbol[self.my_player^1]: 
                        total -= self.neg_fac*(self.bl_pos[i][j]*fac)


        for k in range(2):
            for i in range(3):
                num_player = row[k][i].count(self.pl_symbol[self.my_player])
                num_empty = row[k][i].count('-')
                num_opp = row[k][i].count(self.pl_symbol[self.my_player^1])
                if num_opp == 0 or num_player == 0:
                    total += row_tot[k][i]
                #     total += self.pos_fac*(self.num_cost[num_player])
                # elif num_player == 0 and num_opp > 0:
                #     total -= self.neg_fac*(self.num_cost[num_player])

        for k in range(2):
            for i in range(3):
                num_player = col[k][i].count(self.pl_symbol[self.my_player])
                num_empty = col[k][i].count('-')
                num_opp = col[k][i].count(self.pl_symbol[self.my_player^1])
                if num_opp == 0 or num_player == 0:
                    total += col_tot[k][i]
                #     total += self.pos_fac*(self.num_cost[num_player])
                # elif num_player == 0 and num_opp > 0:
                #     total -= self.neg_fac*(self.num_cost[num_player])

        for k in range(2):
            for i in range(2):
                num_player = diag[k][i].count(self.pl_symbol[self.my_player])
                num_empty = diag[k][i].count('-')
                num_opp = diag[k][i].count(self.pl_symbol[self.my_player^1])
                if num_opp == 0 or num_player == 0:
                    total += diag_tot[k][i]
                #     total += self.pos_fac*(self.num_cost[num_player])
                # elif num_player == 0 and num_opp > 0:
                #     total -= self.neg_fac*(self.num_cost[num_player])

        if total == 0:
            for k in range(2):
                for i in range(3):
                    for j in range(3):
                        total += cost[k][i][j]

        return total

    def find_smallboard_cost(self, board, player, r_no, c_no, b_no):
        row = []
        col = []
        diag = [[], []]
        for _ in range(3):
            row.append([])
            col.append([])
        
        col_tot = [0]*3
        row_tot = [0]*3
        diag_tot = [0]*2
        
        total = 0
        fac = 500
        r_start = 3*r_no
        c_start = 3*c_no
        
        for i in range(r_start, r_start+3):
            for j in range(c_start,  c_start+3):
                row[i%3].append(board.big_boards_status[b_no][i][j])

        for i in range(r_start, r_start+3):
            for j in range(c_start, c_start+3):
                col[j%3].append(board.big_boards_status[b_no][j][i])

        diag[0].append(row[0][0])
        diag[0].append(row[1][1])
        diag[0].append(row[2][2])
        
        diag[1].append(row[0][2])
        diag[1].append(row[1][1])
        diag[1].append(row[2][0])
        
        
        for i in range(3):
            for j in range(3):
                if row[i][j] == self.pl_symbol[self.my_player]:
                    total += self.pos_fac*self.bl_pos[i][j]*fac
                elif row[i][j] == self.pl_symbol[self.my_player^1]:
                    total -= self.neg_fac*self.bl_pos[i][j]*fac
        
        for i in range(3):
            num_player = row[i].count(self.pl_symbol[self.my_player])
            num_empty = row[i].count('-')
            num_opp = row[i].count(self.pl_symbol[self.my_player^1])
            if num_opp == 0:
                total += self.pos_fac*(self.num_cost[num_player])
            elif num_player == 0:
                total -= self.neg_fac*(self.num_cost[num_player])
            if player == self.my_player:
                if num_opp == 2 and num_player == 1:
                    total += 10000

        for i in range(3):
            num_player = col[i].count(self.pl_symbol[self.my_player])
            num_empty = col[i].count('-')
            num_opp = col[i].count(self.pl_symbol[self.my_player^1])
            if num_opp == 0:
                total += self.pos_fac*(self.num_cost[num_player])
            elif num_player == 0:
                total -= self.neg_fac*(self.num_cost[num_player])
            if player == self.my_player:
                if num_opp == 2 and num_player == 1:
                    total += 10000

        for i in range(2):
            num_player = diag[i].count(self.pl_symbol[self.my_player])
            num_empty = diag[i].count('-')
            num_opp = diag[i].count(self.pl_symbol[self.my_player^1])
            if num_opp == 0:
                total += self.pos_fac*(self.num_cost[num_player])
            elif num_player == 0:
                total -= self.neg_fac*(self.num_cost[num_player])
            if player == self.my_player:
                if num_opp == 2 and num_player == 1:
                    total += 10000
        
        return total
    
    def board_hash(self, board):
        self.transp_table = {}
        for k in xrange(2):
            for i in xrange(3):
                for j in xrange(3):
                    val = 0
                    cnt = 0
                    for p in xrange(3):
                        for q in xrange(3):
                            x = board.big_boards_status[k][3*i+p][3*j+q]
                            if(x == self.pl_symbol[self.my_player]):
                                val ^= self.small_board_zobrist[k][2*cnt]
                            elif(x == self.pl_symbol[(self.my_player)^1]):
                                val ^= self.small_board_zobrist[k][2*cnt+1]
                            cnt += 1

                    self.small_board_hash[k][i][j] = val

