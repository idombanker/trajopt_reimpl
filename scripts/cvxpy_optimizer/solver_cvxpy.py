import cvxpy
import numpy as np
from cvxpy.constraints import constraint

import cvxpy.lin_ops.lin_op as lo


class ConvexOptimizer:

    def __init__(self):
        self.joints = None
        self.samples = None
        self.duration = None
        self.x = None
        self.objective = 0
        self.constraints = []

        self.problem = None

    def init(self, joints, samples, duration):
        self.joints = joints
        self.samples = samples
        self.duration = duration
        self.x = cvxpy.Variable((samples, len(joints)))
        self.model_problem()
        self.init_problem()


    def model_problem1(self):
        joints = self.joints.values()
        for i in range(len(joints)):
            for t in range((self.samples - 1)):
                # min_vel = - joints[i].limit.velocity * self.duration / float(self.samples - 1)
                # max_vel = joints[i].limit.velocity * self.duration / float(self.samples - 1)
                # lower_limit = joints[i].limit.lower
                # upper_limit = joints[i].limit.upper
                # start = joints[i].states.start
                # end = joints[i].states.end
                min_vel = - joints[i]["limit"]["velocity"] * self.duration / float(self.samples - 1)
                max_vel = joints[i]["limit"]["velocity"] * self.duration / float(self.samples - 1)
                lower_limit = joints[i]["limit"]["lower"]
                upper_limit = joints[i]["limit"]["upper"]
                start = joints[i]["states"]["start"]
                end = joints[i]["states"]["end"]
                self.objective += cvxpy.sum_squares(self.x[t + 1, i] - self.x[t, i])
                self.constraints += [self.x[t + 1, i] - self.x[t, i] <= max_vel,
                                min_vel <= self.x[t + 1, i] - self.x[t, i]]
                self.constraints += [lower_limit <= self.x, self.x <= upper_limit]
                self.constraints += [self.x[0, i] == start, self.x[self.samples - 1, i] == end]

    def model_problem(self):
        joints = self.joints.values()
        for i in range(len(joints)):
            for t in range((self.samples - 1)):
                # min_vel = - joints[i].limit.velocity * self.duration / float(self.samples - 1)
                # max_vel = joints[i].limit.velocity * self.duration / float(self.samples - 1)
                # lower_limit = joints[i].limit.lower
                # upper_limit = joints[i].limit.upper
                # start = joints[i].states.start
                # end = joints[i].states.end
                min_vel = - joints[i]["limit"]["velocity"] * self.duration / float(self.samples - 1)
                max_vel = joints[i]["limit"]["velocity"] * self.duration / float(self.samples - 1)
                lower_limit = joints[i]["limit"]["lower"]
                upper_limit = joints[i]["limit"]["upper"]
                start = joints[i]["states"]["start"]
                end = joints[i]["states"]["end"]
                self.objective += cvxpy.sum_squares(self.x[t + 1, i] - self.x[t, i])
                self.constraints += [self.x[t + 1, i] - self.x[t, i] <= max_vel,
                                min_vel <= self.x[t + 1, i] - self.x[t, i]]
                self.constraints += [lower_limit <= self.x, self.x <= upper_limit]
                self.constraints += [self.x[0, i] == start, self.x[self.samples - 1, i] == end]



    def init_problem(self):
        self.problem = cvxpy.Problem(cvxpy.Minimize(self.objective), self.constraints)

        problem = cvxpy.Problem(cvxpy.Minimize(self.objective), self.constraints)
        expr = cvxpy.transforms.indicator(self.constraints)
        # c = cvxpy.constraints.constraints.Constraints()
        # c.
        self.x.value = [[-0.49197958, - 1.26687622, - 2.0417783]]

        cons = expr * self.x

        print cons.shape, len(self.constraints), self.x.shape
        # for c in cons:
        #     print c
        # print cons[0]
        # data = self.get_problem_data()
        # cons_val = constraint.Constraint(self.constraints)
        # cons_v = cons_val.residual


        # objective = self.objective + cvxpy.norm(cons, 1)
        # self.problem = cvxpy.Problem(cvxpy.Minimize(objective))

        # t = cvxpy.lin_ops.lin_op.LinOp()
        a = 0
        for i, con in enumerate(problem.constraints):
            a += con.residual
        #     # # print con.residual
        #     # e =  con.canonicalize()[1][0]
        #     # # print cvxpy.multiply(con, self.x.value)
        #     # # print self.x.value
        #     # print e

        print a

        cons1_model = a + cons
        obj = self.objective
        penalty = cvxpy.Parameter(nonneg=True)
        obj += penalty * cvxpy.norm(cons1_model, 1)

        problem1 = cvxpy.Problem(cvxpy.Minimize(obj))
        c = problem1.solve()

        print x.value

    def get_problem_data(self):
        data = {}
        # data["P"]= np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["P"].todense())[:self.samples, -self.samples:]
        # data["q"]= np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["q"])[-self.samples:]
        # data["A"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["A"].todense())[::, -self.samples:]
        # data["G"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["F"].todense())[::2]
        # data["ubG"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["G"])
        # data["b"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["b"])[-self.samples:]
        # # data["G"] = np.vstack([data["G"], -data["G"]])
        # data["lbG"] = np.zeros(data["ubG"].shape)
        # # data["lbG"] = np.vstack([data["ubG"], -data["ubG"]]).flatten()
        # # data["ubG"] = np.vstack([data["ubG"], -data["ubG"]]).flatten()    `
        # data["lbG"] = -data["ubG"]

        # print data["lbG"]
        # print data["ubG"]
        #
        # print data["G"]

        data["P"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["P"].todense())
        data["q"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["q"])
        data["A"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["A"].todense())
        data["G"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["F"].todense())
        data["ubG"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["G"])
        data["b"] = np.asarray(self.problem.get_problem_data(cvxpy.OSQP)[0]["b"])
        # data["G"] = np.vstack([data["G"], -data["G"]])
        data["lbG"] = np.zeros(data["ubG"].shape)
        # data["lbG"] = np.vstack([data["ubG"], -data["ubG"]]).flatten()
        # data["ubG"] = np.vstack([data["ubG"], -data["ubG"]]).flatten()    `
        data["lbG"] = -data["ubG"]

        return data

    def solve(self, solver="ECOS"):
        self.problem.solve(solver=solver, verbose=False)
        return np.asarray(self.x.value.T)