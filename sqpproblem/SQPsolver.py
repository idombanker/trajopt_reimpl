import numpy as np
import cvxpy
import warnings
import copy


class SQPsolver:
    def __init__(self, problem, solver):

        self.P = problem.P
        self.q = problem.q
        self.G = problem.G
        self.lb = problem.lb
        self.ub = problem.ub
        self.lbG = problem.lbG
        self.ubG = problem.ubG
        self.A = problem.A
        self.b = problem.b
        self.initial_guess = problem.initial_guess
        self.solver = solver

    def displayProblem(self):
        print ("P")
        print (self.P)
        print ("q")
        print (self.q)
        print ("G")
        print (self.G)
        print ("lb")
        print (self.lb)
        print ("ub")
        print (self.ub)
        print ("lbG")
        print (self.lbG)
        print ("ubG")
        print (self.ubG)
        print ("b")
        print (self.b)
        print ("A")
        print (self.A)

    def evaluate_constraints(self, x_k):
        print x_k
        cons1 = np.subtract(np.matmul(self.G, x_k), self.ubG)
        cons2 = np.add(np.matmul(-self.G, x_k), self.lbG)
        cons3 = np.subtract(np.matmul(self.A, x_k), self.b)
        return cons1.flatten(), cons2.flatten(), cons3.flatten()

    def get_constraints_grad(self):
        cons1_grad = self.G
        cons2_grad = -self.G
        cons3_grad = self.A
        return cons1_grad, cons2_grad, cons3_grad

    def get_objective_grad_and_hess(self, x_k):
        model_grad = 0.5 * np.matmul((self.P + self.P.T), x_k)
        model_hess = 0.5 * (self.P + self.P.T)
        return model_grad, model_hess

    def get_model_objective(self, x_k, penalty, p):
        cons1_at_xk, cons2_at_xk, cons3_at_xk = self.evaluate_constraints(x_k)
        cons1_grad_at_xk, cons2_grad_at_xk, cons3_grad_at_xk = self.get_constraints_grad()
        cons1_model = cons1_at_xk + cons1_grad_at_xk * p
        cons2_model = cons2_at_xk + cons2_grad_at_xk * p
        cons3_model = cons3_at_xk + cons3_grad_at_xk * p

        objective_grad_at_xk, objective_hess_at_xk = self.get_objective_grad_and_hess(x_k)
        objective_at_xk = self.get_actual_objective(x_k, penalty)
        model = objective_at_xk.value + objective_grad_at_xk * p + 0.5 * cvxpy.quad_form(p, objective_hess_at_xk)

        model += penalty * (cvxpy.norm1(cons1_model) + cvxpy.norm1(cons2_model) + cvxpy.norm1(cons3_model))

        return model, objective_at_xk

    def get_actual_objective(self, xk, penalty):
        x = cvxpy.Variable(self.P.shape[0])
        x.value = copy.copy(xk)
        objective = 0.5 * cvxpy.quad_form(x, self.P) + self.q * x
        constraints1 = cvxpy.norm1(self.G * x - self.ubG.flatten())
        constraints2 = cvxpy.norm1(-self.G * x + self.lbG.flatten())
        constraints3 = cvxpy.norm1(self.A * x - self.b.flatten())
        objective += penalty * (constraints1 + constraints2 + constraints3)
        return objective

    def sovle_problem(self, xk, penalizer, p, delta):
        model_objective, actual_objective = self.get_model_objective(xk, penalizer, p)
        constraints = [cvxpy.norm(p, "inf") <= delta]
        problem = cvxpy.Problem(cvxpy.Minimize(model_objective), constraints)
        result = problem.solve(solver=self.solver, warm_start= True, verbose= False)
        return p.value, model_objective, actual_objective, problem.status

    def approx_equal(self, x, y, tolerance=0.001):
        return abs(x - y) <= 0.5 * tolerance * (x + y)

    def get_constraints_norm(self, x_k):
        con1, con2, con3 = self.evaluate_constraints(x_k)
        max_con1 = (np.linalg.norm(con1, np.inf))
        max_con2 = (np.linalg.norm(con2, np.inf))
        max_con3 = (np.linalg.norm(con3, np.inf))

        return max_con1, max_con2, max_con3

    def solveSQP(self, initial_guess= None):
        x = cvxpy.Variable(self.P.shape[0])
        p = cvxpy.Variable(x.shape[0])
        penalty = cvxpy.Parameter(nonneg= True)
        penalty.value = 1
        # x_0 = np.array([0.2, 0.6, 0.8])
        # print self.initialX
        # x_0 = np.array([2, 2, 2.0, 2, 2, 2.0, 2, 2, 2.0, 2, 2, 2.0])
        # x_0 = np.full((1, 3), 4.0).flatten()
        # x_0 = self.initialGuess
        # x_0 = self.initialX

        if initial_guess is None:
            x_0 = self.initial_guess
        else:
            x_0 = initial_guess
        p_0 = np.zeros(p.shape[0])
        trust_box_size = 2
        max_penalty = 1e4
        min_trust_box_size = 1e-4
        x_k = copy.copy(x_0)
        max_trust_box_size = 5

        trust_shrink_ratio = 0.25
        min_model_improve = 1e-4;
        trust_expand_ratio = 2

        trust_good_region_ratio = 0.75
        max_iteration = 20
        iteration_count = 0

        min_model_improve = 1e-4;
        improve_ratio_threshold = .25;
        min_approx_improve_frac = - float('inf')
        is_converged = False
        isAdjustPenalty = False

        old_rho_k = 0
        new_x_k = copy.copy(x_0)
        min_actual_redution = 1e-1
        min_x_redution = 1e-3

        min_actual_worse_redution = -100
        min_const_violation = 2.4
        con1_norm, con2_norm, con3_norm = self.get_constraints_norm(x_k)
        same_trust_region_count = 0
        old_trust_region = 0

        min_equality_norm = 1e-3
        while abs(con3_norm.all()) <= min_equality_norm or penalty.value <= max_penalty:
            # print "penalty ", penalty.value
            while iteration_count < max_iteration:
                iteration_count += 1
                # print "iteration_count", iteration_count
                while trust_box_size >= min_trust_box_size:
                    p_k, model_objective_at_p_k, actual_objective_at_x_k, solver_status = self.sovle_problem(x_k,
                                                                                                             penalty, p,
                                                                                                             trust_box_size)
                    # print "iteration_count in trust loop", iteration_count


                    # print "pk ", p_k, solver_status

                    actual_objective_at_x_plus_p_k = self.get_actual_objective(x_k + p_k, penalty)
                    model_objective_at_p_0 = self.get_actual_objective(p_0, penalty)

                    # print "objective_at_x_plus_p_k", actual_objective_at_x_plus_p_k.value
                    # print "model_objective_at_x_plus_p_k", model_objective_at_p_0.value
                    # print "actual xk, xk1", actual_objective_at_x_plus_p_k.value, actual_objective_at_x_k.value
                    # print "model p0, pk",model_objective_at_p_0.value, model_objective_at_p_k.value

                    actual_reduction = actual_objective_at_x_plus_p_k.value - actual_objective_at_x_k.value
                    predicted_reduction = model_objective_at_p_0.value - model_objective_at_p_k.value

                    rho_k = actual_reduction / predicted_reduction

                    print "rho_k", rho_k, abs(actual_reduction)
                    print x_k
                    print "x_k + pk ", x_k + p_k, trust_box_size, penalty.value, abs(actual_reduction)
                    con1_norm, con2_norm, con3_norm = self.get_constraints_norm(x_k)
                    # max_con1 = (np.linalg.norm(con1, np.inf))
                    # max_con2 = (np.linalg.norm(con2, np.inf))
                    # print "max_con1, max_con2", con1_norm, con2_norm, actual_reduction
                    max_p_k = (np.linalg.norm(p_k, np.inf))
                    if solver_status == cvxpy.INFEASIBLE or solver_status == cvxpy.INFEASIBLE_INACCURATE or solver_status == cvxpy.UNBOUNDED or solver_status == cvxpy.UNBOUNDED_INACCURATE:
                        # print problem.status
                        # Todo: throw error when problem is not solved
                        break
                    # print con3_norm
                    if old_rho_k == rho_k:
                        # print "rho_k are same"
                        isAdjustPenalty = True
                        break
                    #
                    if abs(actual_reduction) <= min_actual_redution and abs(con3_norm) <= min_equality_norm:
                        if con1_norm + con2_norm >= min_const_violation:
                            print "infeasible intial guess"
                            is_converged = True  # to force loop exit
                            break
                        print "actual reduction is very small, so converged to optimal solution"
                        x_k += p_k
                        is_converged = True
                        break

                    if con1_norm + con2_norm <= min_const_violation or abs(con3_norm) <= min_equality_norm:
                        print "constraint violations are satisfied, so converged to optimal solution"
                        x_k += p_k
                        is_converged = True
                        break

                    if abs((np.linalg.norm(x_k - (x_k + p_k), np.inf))) <= min_x_redution:
                        if con1_norm + con2_norm >= min_const_violation and abs(con3_norm) >= min_equality_norm:
                            print "infeasible intial guess"
                            is_converged = True  # to force loop exit
                            break
                        print "improvement in x is very small, so converged to optimal solution"
                        x_k += p_k
                        is_converged = True
                        break

                    if actual_reduction <= min_actual_worse_redution:
                        print "infeasible intial guess"
                        is_converged = True  # to force loop exit
                        break
                    if predicted_reduction / model_objective_at_p_k.value < -float("inf"):
                        # print "need to adjust penalty"
                        isAdjustPenalty = True
                        break
                    if rho_k <= 0.25:
                        trust_box_size *= trust_shrink_ratio
                        # print "shrinking trust region", trust_box_size
                        break
                        x_k = copy.copy(new_x_k)
                    else:
                        # elif rho_k >= 0.75:
                        trust_box_size = min(trust_box_size * trust_expand_ratio, max_trust_box_size)
                        # print "expanding trust region", trust_box_size
                        x_k += p_k
                        new_x_k = copy.copy(x_k)
                        break

                    if trust_box_size < 0.01:
                        isAdjustPenalty = True
                        break
                    if iteration_count >= max_iteration:
                        print "max iterations reached"
                        break

                    if old_trust_region == trust_box_size:
                        same_trust_region_count += 1
                    if same_trust_region_count >= 5:
                        # print "resetting trust region, since trust region size is same for last ", same_trust_region_count, " iterations"
                        trust_box_size = np.fmax(min_trust_box_size, trust_box_size / trust_shrink_ratio * 0.5)
                    old_rho_k = rho_k
                    old_trust_region = copy.copy(trust_box_size)
                if is_converged:
                    break
                trust_box_size = np.fmax(min_trust_box_size, trust_box_size / trust_shrink_ratio * 0.5)
                # if con1_norm + con2_norm <= min_const_violation:
                #     print "constraint violations are satisfied, so converged to optimal solution"
                #     x_k += p_k
                #     is_converged = True
                #     break
            if is_converged or isAdjustPenalty:
                break
            penalty.value *= 10
            iteration_count = 0
        print "start, end", self.b
        print "initial x_0", x_0
        print "final x_k", x_k, trust_box_size, penalty.value
        return solver_status, x_k
#
# class Sample:
#    P = 0
#    q = 0
#    G = 0
#    lbG = 0
#    ubG = 0
#    lb = 0
#    ub = 0
#    A = 0
#    b = 0
#    initial_guess = None
#
# self = Sample()
# self.P = np.array([[2., -4., 0.],
#                    [0., 4., -4.],
#                    [0., 0., 2.]])
# # Make symmetric and not indefinite
# self.P = .5 * (self.P + self.P.T) + 1e-08 * np.eye(3)
#
# self.q = np.array([1., 1., 0.])
# self.G = np.array([[-1., 1., 0.],
#                    [0., -1., 1.],
#                    [1., 0., 0.],
#                    [0., 1., 0.],
#                    [0., 0., 1.]])
# self.start = 0.2
# self.end = 7.0
# self.lb = np.array([-0.3, -0.3, -0.3, -0.3, -0.3])
# self.ub = np.array([0.3, 0.3, 1.1, 1.1, 1.1])
# self.lbG = np.array([-0.3, -0.3, -0.3, -0.3, -0.3])
# self.ubG = np.array([0.3, 0.3, 1.1, 1.1, 1.1])
#
# self.A = np.array([[1., 0., 0.],
#                    [0., 0., 1.],
#                    [1., 0., 0.],
#                    [0., 0., 1.],
#                    [1., 0., 0.],
#                    [0., 0., 1.],
#                    [1., 0., 0.],
#                    [0., 0., 1.],
#                    # [1., 0., 0.],
#                    # [0., 0., 1.],
#                    # [1., 0., 0.],
#                    # [0., 0., 1.]
#                    ])
# self.b = np.array([self.start, self.end,
#                    self.start, self.end,
#                    self.start, self.end,
#                    self.start, self.end,
#                    # self.start, self.end,
#                    # self.start, self.end
#                    ])
# prob = SQPsolver(self, cvxpy.SCS)
# x_0 = np.array([0.2, 0.6, 0.8])
# prob.solveSQP(x_0)
