import time
import numpy as np

from scripts.Planner import Planner1 as planner
import collections
from munch import  *

# # request = collections.OrderedDict()
# request = {}
# request["samples"] = 50
# request["duration"] = 20
# request["joints"] = {}
# request["joints"] = {
#     "lbr_iiwa_joint_1": {
#         "states": {"start": -0.49197958189616936, "end": -2.0417782994426674},
#         "limit": {"lower": -2.96705972839, "upper": 2.96705972839, "velocity": 10},
#     },
#     "lbr_iiwa_joint_2": {
#         "states": {"start": 1.4223062659337982, "end": 0.9444594031189716},
#             "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
#     },
#     # "lbr_iiwa_joint_3": {
#     #     "states": {"start": -1.5688299779644697, "end": -1.591006403858707},
#     #     "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
#     # },
#     # "lbr_iiwa_joint_4": {
#     #     "states": {"start": -1.3135004031364736, "end": -1.9222844444479184},
#     #     "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
#     #  },
#     # "lbr_iiwa_joint_5": {
#     #     "states": {"start": 1.5696229411153653, "end": 1.572303282659756},
#     #     "limit": {"lower": -2.96705972839, "upper": 2.96705972839, "velocity": 10}
#     # },
#     # "lbr_iiwa_joint_6": {
#     #  "states": {"start": 1.5749627479696093, "end": 1.5741716208788483},
#     #  "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
#     # },
#     # "lbr_iiwa_joint_7": {
#     #     "states": {"start": 1.5708037563007493, "end": 1.5716145442929421},
#     #     "limit": {"lower": -3.05432619099, "upper": 3.05432619099, "velocity": 10}
#     # }
# }
# npzfile = np.load('problem_with_collision_constraints.npz')
#
# request = munchify(npzfile['arr_0'])

request = {}
request["samples"] = 30
request["duration"] = 10
request["joints"] = {}
request["joints"] = {
    "lbr_iiwa_joint_1": {
        "states": {"start": -0.49197958189616936, "end": -2.0417782994426674},
        "limit": {"lower": -2.96705972839, "upper": 2.96705972839, "velocity": 10},
        'collision_constraints': {
            'jacobian': [
                [0.03, 0., 0., 0., 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 0.]
            ],
            'initial_signed_distance': [
                [0.56992542]
            ],
            'limits': {
                'upper': 8,
                'lower': 2
            },
            'normal': [
                [-2.83286033e-01],
                [9.59035465e-01],
                [2.40965016e-17]
            ]
        }
    },
    "lbr_iiwa_joint_2": {
        "states": {"start": 1.4223062659337982, "end": 0.9444594031189716},
            "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
        'collision_constraints': {
            'jacobian': [
                [-5.90000004e-02, -3.31987955e-02, 0.00000000e+00,
                 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00
                 ],
                [3.00000014e-04, -2.57262465e-02, 0.00000000e+00,
                 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00
                 ],
                [9.76270852e-19, 3.63763860e-02, 0.00000000e+00,
                 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00
                 ]
            ],
            'initial_signed_distance': [
                [0.5226252]
            ],
            'limits': {
                'upper': 8,
                'lower': 2
            },
            'normal': [
                [-3.12383895e-01],
                [9.49955947e-01],
                [-2.62526036e-17]
            ]
        }
    },
    "lbr_iiwa_joint_3": {
        "states": {"start": -1.5688299779644697, "end": -1.591006403858707},
        "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
        'collision_constraints': {
            'jacobian': [
                [9.49485195e-02, -1.14193005e-01, -8.15515542e-02,
                 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00
                 ],
                [-1.61241579e-01, -8.84898615e-02, 1.02500758e-01,
                 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00
                 ],
                [-5.97683772e-19, -1.85611804e-01, -2.36540213e-02,
                 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00
                 ]
            ],
            'initial_signed_distance': [
                [0.54124091]
            ],
            'limits': {
                'upper': 8,
                'lower': 2
            },
            'normal': [
                [-6.12193539e-01],
                [7.90707956e-01],
                [2.53595585e-17]
            ]
        }
    },
    # "lbr_iiwa_joint_4": {
    #     "states": {"start": -1.3135004031364736, "end": -1.9222844444479184},
    #     "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
    #     'collision_constraints': {
    #         'jacobian': [
    #             [1.89617972e-01, -5.03599247e-02, -2.55133869e-02, -6.55051278e-02, 0.00000000e+00, 0.00000000e+00,
    #              0.00000000e+00
    #              ],
    #             [-3.31156301e-01, -3.90246400e-02, 2.68078929e-02, -2.01516355e-03, 0.00000000e+00, 0.00000000e+00,
    #              0.00000000e+00
    #              ],
    #             [-5.27355971e-19, -3.77908335e-01, -5.28273168e-02,
    #              3.97105747e-03, 0.00000000e+00, 0.00000000e+00,
    #              0.00000000e+00
    #              ]
    #         ],
    #         'initial_signed_distance': [
    #             [0.56549429]
    #         ],
    #         'limits': {
    #             'upper': 8,
    #             'lower': 2
    #         },
    #         'normal': [
    #             [-8.11238378e-01],
    #             [5.84715567e-01],
    #             [4.85666719e-17]
    #         ]
    #     }
    #  },
    # "lbr_iiwa_joint_5": {
    #     "states": {"start": 1.5696229411153653, "end": 1.572303282659756},
    #     "limit": {"lower": -2.96705972839, "upper": 2.96705972839, "velocity": 10},
    #     'collision_constraints': {
    #         'jacobian': [
    #             [1.97416647e-01, -9.08447869e-02, -5.62554437e-02, -5.57285813e-02, 1.46868839e-02, 0.00000000e+00,
    #              0.00000000e+00
    #              ],
    #             [-5.11322608e-01, -7.03969587e-02, 5.44464495e-02, -1.84763071e-01, 7.42610356e-02, 0.00000000e+00,
    #              0.00000000e+00
    #              ],
    #             [-1.45890242e-19, -5.25097277e-01, -1.56759056e-01,
    #              1.05354486e-02, -2.05388219e-02, 0.00000000e+00,
    #              0.00000000e+00
    #              ]
    #         ],
    #         'initial_signed_distance': [
    #             [0.78574064]
    #         ],
    #         'limits': {
    #             'upper': 8,
    #             'lower': 2
    #         },
    #         'normal': [
    #             [-0.8960243],
    #             [0.44400501],
    #             [0.]
    #         ]
    #     }
    # },
    # "lbr_iiwa_joint_6": {
    #  "states": {"start": 1.5749627479696093, "end": 1.5741716208788483},
    #  "limit": {"lower": -2.09439510239, "upper": 2.09439510239, "velocity": 10},
    #     'collision_constraints': {
    #         'jacobian': [
    #             [1.73196668e-01, -3.95972419e-02, -1.83557530e-02, -8.24160784e-02, 5.28451890e-05, -4.29827788e-04,
    #              -0.00000000e+00],
    #             [-7.21977566e-01, -3.06844592e-02, -1.15743501e-02, -3.91044494e-01, 3.90821264e-04, 8.14733448e-05,
    #              0.00000000e+00
    #              ],
    #             [-1.38715428e-17, -6.76773524e-01, -3.04564880e-01,
    #              2.01866490e-02, -5.86231938e-04, -1.22210026e-04,
    #              0.00000000e+00
    #              ]
    #         ],
    #         'initial_signed_distance': [
    #             [0.94646815]
    #         ],
    #         'limits': {
    #             'upper': 8,
    #             'lower': 2
    #         },
    #         'normal': [
    #             [-8.89792368e-01],
    #             [4.56365580e-01],
    #             [-2.91406863e-17]
    #         ]
    #     }
    # },
    # "lbr_iiwa_joint_7": {
    #     "states": {"start": 1.5708037563007493, "end": 1.5716145442929421},
    #     "limit": {"lower": -3.05432619099, "upper": 3.05432619099, "velocity": 10},
    #     'collision_constraints': {
    #         'jacobian': [
    #             [1.78232848e-01, 8.73904627e-03, 1.93631816e-02, -7.97775055e-02, -1.23569633e-02, 5.96341810e-02,
    #              -1.09535371e-03],
    #             [-7.26524255e-01, 6.77205581e-03, -6.01111797e-02, -3.91955363e-01, -5.95836519e-02, -1.26700188e-02,
    #              1.12263952e-03
    #              ],
    #             [-1.73472348e-17, -6.83452253e-01, -3.03372022e-01,
    #              2.00654813e-02, 5.27578990e-03, -3.53793836e-03,
    #              0.00000000e+00
    #              ]
    #         ],
    #         'initial_signed_distance': [
    #             [0.96173253]
    #         ],
    #         'limits': {
    #             'upper': 8,
    #             'lower': 2
    #         },
    #         'normal': [
    #             [-8.96469921e-01],
    #             [4.43104594e-01],
    #             [-5.37769502e-18]
    #         ]
    #     }
    # }
}


# print request
request = munchify(request)

temp = 1
plan = planner.TrajectoryOptimizationPlanner()

start = time.time()
# plan.init(problem=request)
plan.init(joints=request["joints"], samples=request["samples"], duration=request["duration"],
          solver=None, solver_config=None, solver_class=0,
          decimals_to_round=3, verbose=False)
plan.calculate_trajectory()
end = time.time()
# plan.display_problem()
print plan.get_trajectory().trajectory_by_name
print("computation time: ",end - start)

