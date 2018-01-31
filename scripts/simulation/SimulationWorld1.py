import logging
import pybullet as sim
import time
import numpy as np
from scripts.Robot import Robot
from munch import *
import os

CYLINDER = sim.GEOM_CYLINDER
BOX = sim.GEOM_BOX


class SimulationWorld():
    def __init__(self, urdf_file=None):

        if urdf_file is None:
            main_logger_name = "Trajectory_Planner"
            verbose = "DEBUG"
            # verbose = False
            self.logger = logging.getLogger(main_logger_name)
            self.setup_logger(main_logger_name, verbose)
        else:
            self.logger = logging.getLogger("Trajectory_Planner." + __name__)

        # self.gui = sim.connect(sim.DIRECT)
        self.gui = sim.connect(sim.GUI)
        # self.gui = sim.connect(sim.SHARED_MEMORY)
        sim.configureDebugVisualizer(sim.COV_ENABLE_RENDERING, 0)
        home = os.path.expanduser('~')
        # location_prefix = '/home/mahe/masterThesis/bullet3/data/'
        # location_prefix = '/home/mahesh/libraries/bullet3/data/'
        location_prefix = home + '/masterThesis/bullet3/data/'
        if urdf_file is None:
            urdf_file = location_prefix + "kuka_iiwa/model.urdf"
        self.robot = Robot.Robot(urdf_file)
        self.robot_id = -1
        self.table_id = -1
        self.joint_name_to_id = {}
        self.no_of_joints = -1
        self.start_state_for_traj_planning = {}
        self.end_state_for_traj_planning = {}
        pland_id = self.place_items_from_urdf(urdf_file=location_prefix + "plane.urdf",
                                              position=[0, 0, 0.0])

        self.table_id = self.place_items_from_urdf(urdf_file=location_prefix + "table/table.urdf",
                                                   position=[0, 0, 0.0])

        self.robot_id = self.place_items_from_urdf(urdf_file, position=[0, 0.25, 0.6])

        self.planning_group = []
        self.planning_samples = 0
        self.lower_threshold_collision_limit = 0.3
        self.upper_threshold_collision_limit = 1
        self.collision_check_distance = 0.1

        self.end_effector_index = 6
        use_real_time_simulation = 0
        fixed_time_step = 0.01
        if use_real_time_simulation:
            sim.setRealTimeSimulation(use_real_time_simulation, self.gui)
        else:
            sim.setTimeStep(fixed_time_step, self.gui)

        sim.setGravity(0, 0, -10)
        self.no_of_joints = sim.getNumJoints(self.robot_id)
        self.setup_joint_id_to_joint_name()

        # self.cylinder_id = self.create_constraint(shape=CYLINDER, height=0.28, radius=0.1,
        #                                           position=[-0.17, -0.22, 0.9], mass=1)
        self.box_id = self.create_constraint(shape=BOX, size=[0.1, 0.27, 0.25],
                                             position=[0.28, -0.25, 0.9], mass=100)
        self.collision_constraints = None

        sim.configureDebugVisualizer(sim.COV_ENABLE_RENDERING, 1)

        if urdf_file is not None:
            # start_state = {
            #     'lbr_iiwa_joint_1': -1.570,
            #     'lbr_iiwa_joint_2': 1.571,
            #     'lbr_iiwa_joint_3': -1.570,
            #     'lbr_iiwa_joint_4': -1.570,
            #     'lbr_iiwa_joint_5': 1.571,
            #     'lbr_iiwa_joint_6': 1.571,
            #     'lbr_iiwa_joint_7': 1.571
            # }
            start_state = {'lbr_iiwa_joint_5': 1.5855963769735366, 'lbr_iiwa_joint_4': -0.8666279970481103,
                           'lbr_iiwa_joint_7': 1.5704531145724918, 'lbr_iiwa_joint_6': 1.5770985888989753,
                           'lbr_iiwa_joint_1': -2.4823357809267463, 'lbr_iiwa_joint_3': -1.5762726255540713,
                           'lbr_iiwa_joint_2': 1.4999975516996142}
            self.reset_joint_states(start_state)

            # else:

    def setup_logger(self, main_logger_name, verbose=False, log_file=False):

        # creating a formatter
        formatter = logging.Formatter('-%(asctime)s - %(name)s - %(levelname)-8s: %(message)s')

        # create console handler with a debug log level
        log_console_handler = logging.StreamHandler()
        if log_file:
            # create file handler which logs info messages
            logger_file_handler = logging.FileHandler(main_logger_name + '.log', 'w', 'utf-8')
            logger_file_handler.setLevel(logging.INFO)
            # setting handler format
            logger_file_handler.setFormatter(formatter)
            # add the file logging handlers to the logger
            self.logger.addHandler(logger_file_handler)

        if verbose == "WARN":
            self.logger.setLevel(logging.WARN)
            log_console_handler.setLevel(logging.WARN)

        elif verbose == "INFO" or verbose is True:
            self.logger.setLevel(logging.INFO)
            log_console_handler.setLevel(logging.INFO)

        elif verbose == "DEBUG":
            self.logger.setLevel(logging.DEBUG)
            log_console_handler.setLevel(logging.DEBUG)

        # setting console handler format
        log_console_handler.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(log_console_handler)

    def create_constraint(self, shape, mass, position, size=None, radius=None, height=None, orientation=None):
        if position is not None:
            if radius is not None:
                col_id = sim.createCollisionShape(shape, radius=radius, height=height)
                vis_id = sim.createCollisionShape(shape, radius=radius, height=height)
            if size is not None:
                col_id = sim.createCollisionShape(shape, halfExtents=size)
                vis_id = sim.createCollisionShape(shape, halfExtents=size)
            shape_id = sim.createMultiBody(mass, col_id, vis_id, position)

        return shape_id

    def place_items_from_urdf(self, urdf_file, position, orientation=None, use_fixed_base=True):

        if orientation is None:
            urdf_id = sim.loadURDF(urdf_file, basePosition=position, useFixedBase=use_fixed_base)
        else:
            urdf_id = sim.loadURDF(urdf_file, basePosition=position,
                                   baseOrientation=orientation, useFixedBase=use_fixed_base)

        return urdf_id

    def run_simulation(self):
        iteration_count = 0
        while 1:
            if iteration_count < 1:
                iteration_count += 1
                # goal_state = {
                #     'lbr_iiwa_joint_1': -2.0417782994426674,
                #     'lbr_iiwa_joint_2': 0.9444594031189716,
                #     'lbr_iiwa_joint_3': -1.591006403858707,
                #     'lbr_iiwa_joint_4': -1.9222844444479184,
                #     'lbr_iiwa_joint_5': 1.572303282659756,
                #     'lbr_iiwa_joint_6': 1.5741716208788483,
                #     'lbr_iiwa_joint_7': 1.5716145442929421
                # }
                # start_state = {
                #     'lbr_iiwa_joint_1': -1.570,
                #     'lbr_iiwa_joint_2': 1.571,
                #     'lbr_iiwa_joint_3': -1.570,
                #     'lbr_iiwa_joint_4': -1.570,
                #     'lbr_iiwa_joint_5': 1.571,
                #     'lbr_iiwa_joint_6': 1.571,
                #     'lbr_iiwa_joint_7': 1.571
                # }
                start_state = {'lbr_iiwa_joint_5': 1.5855963769735366, 'lbr_iiwa_joint_4': -0.8666279970481103,
                               'lbr_iiwa_joint_7': 1.5704531145724918, 'lbr_iiwa_joint_6': 1.5770985888989753,
                               'lbr_iiwa_joint_1': -2.4823357809267463, 'lbr_iiwa_joint_3': -1.5762726255540713,
                               'lbr_iiwa_joint_2': 1.4999975516996142}
                goal_state = {'lbr_iiwa_joint_5': 1.5979105177314896, 'lbr_iiwa_joint_4': -0.5791571346767671,
                              'lbr_iiwa_joint_7': 1.5726221954434347, 'lbr_iiwa_joint_6': 1.5857854098720727,
                              'lbr_iiwa_joint_1': -0.08180533826032865, 'lbr_iiwa_joint_3': -1.5873548294514912,
                              'lbr_iiwa_joint_2': 1.5474152457596664}

                # startState = [-1.5708022241650113, 1.5711988957726704, -1.57079632679,
                #               -1.5707784259568982, 1.5713463278825928, 1.5719498333358852, 1.5707901876998593]
                group1_test = ['lbr_iiwa_joint_1']

                group1 = ['lbr_iiwa_joint_1', 'lbr_iiwa_joint_2', 'lbr_iiwa_joint_3']
                group2 = ['lbr_iiwa_joint_4', 'lbr_iiwa_joint_5', 'lbr_iiwa_joint_6', 'lbr_iiwa_joint_7']
                duration = 20
                samples = 20
                full_arm = group1 + group2
                # full_arm = group1_test
                lower_d_safe = 0.3
                upper_d_safe = 8
                self.reset_joint_states(start_state)
                self.step_simulation_for(3)
                time.sleep(1)
                distance = self.collision_check_distance
                self.plan_trajectory(goal_state.keys(), goal_state, samples, duration, lower_d_safe, upper_d_safe, collision_check_distance=distance)
                self.execute_trajectory(full_arm)
                # import sys
                # sys.exit()

    def get_joint_ids_from_planning_group(self, group):
        joint_ids = []
        for joint in group:
            joint_ids.append(self.joint_name_to_id[joint])
        return joint_ids

    def get_collision_infos(self, initial_trajectory, group, distance=0.20):

        # print initial_trajectory

        collsiion_infos = self.formulate_collision_infos(initial_trajectory, group, distance)

        return collsiion_infos

    def formulate_collision_infos(self, trajectory, group, distance=0.2):
        SIGNED_DISTANCE = 8
        NORMAL = 7
        CLOSEST_POINT = 5

        normal_matrix = []
        initial_signed_distance_matrix = []
        # closest_pts = []
        jacobian = []
        jacobian_matrix = []
        jacobian_matrix1 = []
        normal_T_times_jacobian_matrix = []
        start_state = self.get_current_states_for_given_joints(group)
        link_ids_planning_group = self.get_joint_ids_from_planning_group(group)
        no_collision = True
        time_step_count = 0
        for time_step_of_trajectory in trajectory:
            time_step_count += 1
            normal_T_times_jacobian_of_each_link = []
            initial_signed_distance_of_each_link = []
            jacobian_of_each_link = []
            jacobian_of_each_link1 = []
            normal_of_each_link = []

            for link_index in link_ids_planning_group:
                time_step_of_trajectory = time_step_of_trajectory.reshape((time_step_of_trajectory.shape[0], 1))
                self.reset_joint_states_to(time_step_of_trajectory, group)
                robot_link_state = list(time_step_of_trajectory.flatten())
                zero_vec = [0.0] * len(robot_link_state)
                # if link_index == self.end_effector_index - 2:

                # if link_index == 6 or link_index == 5 or link_index == 4:
                closest_points = sim.getClosestPoints(self.robot_id, self.box_id,
                                                      linkIndexA=link_index, distance=distance)
                if len(closest_points) > 0:
                    if closest_points[0][SIGNED_DISTANCE] < 0:
                        # print "less", link_index
                        closest_point = closest_points[0][CLOSEST_POINT]
                        initial_signed_distance_of_each_link.append(closest_points[0][SIGNED_DISTANCE])

                        normal = np.asarray(closest_points[0][NORMAL]).reshape(3, 1)
                        normal_of_each_link.append(normal)
                        # jac_t, jac_r = sim.calculateJacobian(self.robot_id, link_index, closest_point,
                        jac_t, jac_r = sim.calculateJacobian(self.robot_id, link_index, [0, 0, 0],
                                                             robot_link_state,
                                                             zero_vec, zero_vec)
                        # jacobian.append(jac_t)
                        normal_times_jacobian = np.matmul(normal.T, np.asarray(jac_t)).tolist()
                        temp = np.zeros((1, len(group))).tolist() * (time_step_count - 1) + normal_times_jacobian + np.zeros(
                            (1, len(group))).tolist() * (len(trajectory) - time_step_count)
                        temp =  np.hstack(temp)
                        normal_T_times_jacobian_of_each_link.append(temp)
                        jacobian_of_each_link.append(jac_t)
                        # temp1 = [[0] * len(group)] * 3 * (time_step_count - 1) + list(jac_t) + [[0] * len(
                        #     group)] * 3 * (len(trajectory) - time_step_count)
                        # temp1 = np.zeros((3, len(group))).tolist() * (
                        # time_step_count - 1) + list(jac_t) + np.zeros(
                        #     (3, len(group))).tolist() * (len(trajectory) - time_step_count)

                        # temp1 = np.append(np.zeros((3, len(group))).tolist() * (
                        #     time_step_count - 1) + np.asarray(jac_t), np.zeros((3, len(group))).tolist() * (
                        #     time_step_count - 1))
                        # jacobian_of_each_link1.append(temp1)
                        # print np.asarray(temp1)

            if len(normal_of_each_link) > 0:
                normal_matrix.append(np.vstack(normal_of_each_link))

                # normal_matrix.append(normal_of_each_link)

            if len(jacobian_of_each_link) > 0:
                jacobian_matrix.append(np.vstack(jacobian_of_each_link))

            if len(jacobian_of_each_link1) > 0:
                jacobian_matrix1.append(np.vstack(jacobian_of_each_link1))

            if len(initial_signed_distance_of_each_link) > 0:
                initial_signed_distance_matrix.append(np.vstack(initial_signed_distance_of_each_link))

            if len(normal_T_times_jacobian_of_each_link) > 0:
                normal_T_times_jacobian_matrix.append(np.vstack(normal_T_times_jacobian_of_each_link))

        if len(initial_signed_distance_matrix) > 0:
            initial_signed_distance_matrix = np.vstack(initial_signed_distance_matrix)

        if len(normal_T_times_jacobian_matrix) > 0:
            normal_T_times_jacobian_matrix = np.vstack(normal_T_times_jacobian_matrix)

        # print "normal", np.vstack(normal_matrix).shape
        # print "initial SD", np.vstack(initial_signed_distance_matrix).shape
        # print "normal times jaco", np.vstack(normal_T_times_jacobian_matrix).shape
        # jacobian_matrix =  np.vstack(jacobian_matrix)
        # jacobian_matrix1 =  np.vstack(jacobian_matrix1)
        # print jacobian_matrix
        # print jacobian_matrix.shape
        # print jacobian_matrix1.shape


        self.reset_joint_states(start_state, group)

        return initial_signed_distance_matrix, normal_T_times_jacobian_matrix

    def formulate_collision_infos2(self, trajectory, group, distance=0.2):

        SIGNED_DISTANCE = 8
        NORMAL = 7
        CLOSEST_POINT = 5

        normal_matrix = []
        initial_signed_distance_matrix = []
        # closest_pts = []
        jacobian = []
        jacobian_matrix = []
        normal_T_times_jacobian_matrix = []
        start_state = self.get_current_states_for_given_joints(group)
        link_ids_planning_group = self.get_joint_ids_from_planning_group(group)
        no_collision = True
        for time_step_of_trajectory in trajectory:

            normal_T_times_jacobian_of_each_link = []
            initial_signed_distance = []

            for link_index in link_ids_planning_group:

                time_step_of_trajectory = time_step_of_trajectory.reshape((time_step_of_trajectory.shape[0], 1))
                self.reset_joint_states_to(time_step_of_trajectory, group)
                robot_link_state = list(time_step_of_trajectory.flatten())
                zero_vec = [0.0] * len(robot_link_state)


                # if link_index == 6 or link_index == 5 or link_index == 4:
                closest_points = sim.getClosestPoints(self.robot_id, self.box_id,
                                                          linkIndexA=link_index, distance=distance)
                if len(closest_points) > 0:
                    if closest_points[0][SIGNED_DISTANCE] < 0:
                        # print "less", link_index
                        closest_point = closest_points[0][CLOSEST_POINT]
                        initial_signed_distance.append(closest_points[0][SIGNED_DISTANCE])

                        normal = np.asarray(closest_points[0][NORMAL]).reshape(1, 3)
                        jac_t, jac_r = sim.calculateJacobian(self.robot_id, link_index, closest_point,
                                                             robot_link_state,
                                                             zero_vec, zero_vec)
                        # jacobian.append(jac_t)
                        normal_T_times_jacobian_of_each_link.append(np.matmul(normal, np.asarray(jac_t)).flatten())
                    else:
                        # print "more", link_index
                        # jacobian.append(np.asarray(np.zeros((3, len

                        normal_T_times_jacobian_of_each_link.append(np.zeros((1, len(group))).flatten())
                else:
                    # print "el more", link_index
                    # jacobian.append(np.asarray(np.zeros((3, len(group)))))

                    normal_T_times_jacobian_of_each_link.append(np.zeros((1, len(group))).flatten())
                # else:
                    # print "el more", link_index
                    # normal_T_times_jacobian_of_each_link.append(np.zeros((1, len(group))).flatten())
            if len(normal_T_times_jacobian_of_each_link) > 0:
                normal_T_times_jacobian_matrix.append(np.vstack(normal_T_times_jacobian_of_each_link))
                print np.vstack(normal_T_times_jacobian_matrix).shape

            if len(initial_signed_distance) > 0:

                initial_signed_distance_matrix.append(np.hstack(initial_signed_distance))
                print np.asarray(initial_signed_distance_matrix).shape
        if len(normal_T_times_jacobian_matrix) > 0:
            normal_T_times_jacobian_matrix = np.hstack(normal_T_times_jacobian_matrix)
            # jacobian_matrix = jacobian_matrix[~np.all(jacobian_matrix == 0, axis=1)]
            # jacobian_matrix = np.hstack(jacobian_matrix)
        if len(initial_signed_distance_matrix) > 0:

            initial_signed_distance_matrix = np.hstack(initial_signed_distance_matrix)
        # print (normal_T_times_jacobian_matrix)
        print (normal_T_times_jacobian_matrix).shape
        print (initial_signed_distance_matrix).shape
        print (initial_signed_distance_matrix)
        # print jacobian_matrix[~np.all(jacobian_matrix == 0, axis=1)]

        return initial_signed_distance_matrix, normal_matrix, jacobian_matrix

    def formulate_collision_infos1(self, trajectory, group, distance=0.2):

        normal = []
        initial_signed_distance = []
        closest_pts = []
        jacobian = []
        normal_T_times_jacobian = []

        jacobian_matrix = []
        start_state = self.get_current_states_for_given_joints(group)
        link_ids_planning_group = self.get_joint_ids_from_planning_group(group)

        for time_step_of_trajectory in trajectory:
            normal_of_each_link = []
            initial_signed_distance_of_each_link = []
            closest_points_of_each_link = []
            # jacobian_of_each_link = []
            jacobian_matrix_of_each_link = []
            normal_T_times_jacobian_of_each_link = []

            time_step_of_trajectory = time_step_of_trajectory.reshape((time_step_of_trajectory.shape[0], 1))
            self.reset_joint_states_to(time_step_of_trajectory, group)
            robot_link_state = self.get_joint_states(group)[0]
            zero_vec = [0.0] * len(robot_link_state)
            for link_index in link_ids_planning_group:
                # if link_index == 5 or link_index == 6:
                # link_state = sim.getLinkState(self.robot_id, link_index, computeLinkVelocity=1,
                #                               computeForwardKinematics=1)
                # link_postion_in_world_frame = link_state[0]
                closest_points = sim.getClosestPoints(self.robot_id, self.box_id,
                                                      linkIndexA=link_index, distance=distance)
                if len(closest_points) > 0:
                    if closest_points[0][8] < 0:
                        initial_signed_distance_of_each_link.append(closest_points[0][8])
                        normal_of_each_link.append(np.asarray(closest_points[0][7]).reshape(3, 1))
                        closest_points_of_each_link.append(closest_points[0][5])
                        # todo: change closest point from world frame to local frame
                        jac_t, jac_r = sim.calculateJacobian(self.robot_id, link_index, closest_points[0][5],
                                                             robot_link_state,
                                                             zero_vec, zero_vec)
                        jacobian_matrix_of_each_link.append(np.asarray(jac_t))
                        # normal_T_times_jacobian_of_each_link.append(np.matmul(
                        #     np.asarray(closest_points[0][7]).reshape(1, 3), np.asarray(jac_t)))
                        # jacobian_of_each_link.append(np.asarray(jac_t))
                    else:
                        jacobian_matrix_of_each_link.append(np.zeros((3, len(group))))
                        # normal_T_times_jacobian_of_each_link.append(np.zeros((1, len(group))))
                else:
                    jacobian_matrix_of_each_link.append(np.zeros((3, len(group))))
            if len(normal_of_each_link) > 0 and len(jacobian_matrix_of_each_link):
                normal_T_times_jacobian_of_each_link.append(np.matmul(
                    np.hstack(normal_of_each_link), np.asarray(jacobian_matrix_of_each_link)))

            # if len(jacobian_matrix_of_each_link) > 0:
            #     print np.asarray(jacobian_matrix_of_each_link).shape
            # if len(normal_of_each_link) > 0:
            #     print np.asarray(np.vstack(normal_of_each_link)).shape
            if len(normal_T_times_jacobian_of_each_link) > 0:
                print np.asarray(normal_T_times_jacobian_of_each_link).shape
                # print np.vstack(np.hstack(normal_T_times_jacobian_of_each_link).flatten()).shape


            if len(normal_of_each_link) > 0:
                normal.append(np.vstack(normal_of_each_link))

            if len(initial_signed_distance_of_each_link) > 0:
                initial_signed_distance.append(np.vstack(initial_signed_distance_of_each_link))

            if len(jacobian_matrix_of_each_link) > 0:
                jacobian_matrix.append(np.vstack(jacobian_matrix_of_each_link))



        if len(normal) > 0:
            normal = np.hstack(normal)

        if len(initial_signed_distance) > 0:
            initial_signed_distance = np.hstack(initial_signed_distance)

        if len(jacobian_matrix) > 0:
            jacobian_matrix = np.hstack(jacobian_matrix)
        else:
            print "out of collision .. ."

            # if len(jacobian_matrix_of_each_link) > 0:
            #     jacobian.append(jacobian_matrix_of_each_link)
            # if len(initial_signed_distance_of_each_link) > 0:
            #     initial_signed_distance.append(initial_signed_distance_of_each_link)
            # if len(normal_of_each_link) > 0:
            #     normal.append(normal_of_each_link)
            # if len(jacobian_matrix_of_each_link) > 0:
            #     jacobian_matrix.append(jacobian_matrix_of_each_link)

        #
        #         # jacobian = np.asarray(jac_t)
        #         # normal = np.asarray(closest_points[0][7]).reshape(3, 1)
        #
        #         # normal_times_jacobian.append(np.matmul(np.asarray(normal).T, np.asarray(jacobian)))
        #
        #         # print np.asarray(jacobian).shape
        # print np.asarray(jacobian).shape
        # if len(jacobian) > 0:
        #     jacobian = np.hstack(np.asarray(jacobian))

        # if len(normal) > 0:
        #     normal = np.hstack(np.asarray(normal))
        #
        # if len(initial_signed_distance) > 0:
        #     initial_signed_distance = np.hstack(np.asarray(initial_signed_distance))
        #
        # if len(jacobian_matrix) > 0:
        #     jacobian_matrix = np.hstack(jacobian_matrix)
        # else:
        #     print "out of collision .. ."
        # # print "jacobian", jacobian.shape
        print "normal ", normal.shape
        print "initial_signed_distance ", initial_signed_distance.shape
        # print "initial", time_step_of_trajectory.shape
        print "initial_trajectory ", np.asarray(trajectory.flatten()).shape
        print "jacobian_matrix ", jacobian_matrix.shape
        # print "jacobian_matrix ", jacobian_matrix.T
        # self.reset_joint_states(start_state, group)

        return initial_signed_distance, normal, jacobian_matrix
        # for i in jacobian_matrix:
        #     print i
        #
        #
        # jacobian = np.vstack(jacobian)
        # normal = np.vstack(normal)
        # initial_signed_distance = np.vstack(initial_signed_distance).shape
        # normal_times_jacobian = np.vstack(normal_times_jacobian)
        # print "normal_times_jacobian", normal_times_jacobian.shape
        # temp = np.matmul(normal_times_jacobian, initial_trajectory)
        # print temp.shape

    def get_collision_infos1(self, group, lower_d_safe_limit, upper_d_safe_limit, distance=0.2):

        can_execute_trajectory = False
        pos = self.get_joint_states(group)[0]
        zero_vec = [0.0] * len(pos)
        jacobian_by_joint_name = {}
        # for joint_name in group:
        # # result = sim.getLinkState(self.robot_id, self.joint_name_to_id[joint_name], computeLinkVelocity=1,
        # #                           computeForwardKinematics=1)
        # result = sim.getLinkState(self.robot_id, self.end_effector_index, computeLinkVelocity=1,
        #                           computeForwardKinematics=1)
        # com_trn = result[2]
        #
        # # jac_t, jac_r = sim.calculateJacobian(self.robot_id, self.joint_name_to_id[joint_name], com_trn, pos, zero_vec, zero_vec)
        # jac_t, jac_r = sim.calculateJacobian(self.robot_id, self.end_effector_index, com_trn, pos, zero_vec, zero_vec)
        # jac_t = np.asarray(jac_t)
        # print jac_t
        # print "gfda ", jac_t[:, 2]
        # print jac_t[0]
        for joint_name in group:
            # print joint_name
            jacobian = []
            normal = []
            normal_times_jacobian = []
            initial_signed_distance = []

            result = sim.getLinkState(self.robot_id, self.joint_name_to_id[joint_name], computeLinkVelocity=1,
                                      computeForwardKinematics=1)

            com_trn = result[2]

            jac_t, jac_r = sim.calculateJacobian(self.robot_id, self.joint_name_to_id[joint_name], com_trn, pos,
                                                 zero_vec, zero_vec)

            jac_t = np.asarray(jac_t)
            # jacobian_by_joint_name[joint_name] = jac_t[:, self.joint_name_to_id[joint_name]]
            contact_points = sim.getCPoints(self.robot_id, self.box_id,
                                            linkIndexA=self.joint_name_to_id[joint_name], distance=distance)
            # print jac_t
            # print contact_points

            if len(contact_points) > 0:
                # jacobian.append(np.asarray(jac_t[:, self.joint_name_to_id[joint_name]]).reshape(3, 1))
                jacobian.append(np.asarray(jac_t))
                normal.append(np.asarray(contact_points[0][7]).reshape(3, 1))
                initial_signed_distance.append(contact_points[0][8])
                # normal_times_jacobian.append(np.matmul(np.asarray(contact_points[0][7]).reshape(3, 1).T,
                #                                        np.asarray(jac_t)))

            # print "normal", contact_points[0][7]
            # jaco = np.asarray(jac_t[:, self.joint_name_to_id[joint_name]]).reshape(3,1)
            # jaco = np.asarray(jac_t).T
            # self.collision_constraints[joint_name] = munchify({
            #     "jacobian": jaco[self.joint_name_to_id[joint_name]],
            #     "normal": np.asarray(contact_points[0][7]).reshape(3,1),
            #     "initial_signed_distance": contact_points[0][8],
            #     "limits": {"lower": lower_d_safe_limit, "upper": upper_d_safe_limit}
            # })
            # print normal_times_jacobian, initial_signed_distance
            self.collision_constraints[joint_name] = munchify({
                "jacobian": np.vstack(jacobian),
                "normal": np.vstack(normal),
                # "normal_times_jacobian": np.asarray(normal_times_jacobian).T[self.joint_name_to_id[joint_name]],
                "initial_signed_distance": np.vstack(initial_signed_distance),
                "limits": {"lower": lower_d_safe_limit, "upper": upper_d_safe_limit}
            })
            # print joint_name, self.collision_constraints[joint_name]
            # print "self.collision_constraints[lbr_iiwa_joint_1]", self.collision_constraints["lbr_iiwa_joint_1"]
            # print self.collision_constraints

    def update_collsion_infos(self, new_trajectory, delta_trajectory):
        print "updating collision infos . . .. . . ."
        self.robot.planner.trajectory.add_trajectory(new_trajectory)
        trajectory = np.split(new_trajectory, self.planning_samples)
        collision_infos = self.get_collision_infos(trajectory, self.planning_group, distance=self.collision_check_distance)

        constraints, lower_limit, upper_limit = self.robot.planner.problem.update_collision_infos(collision_infos,
                                                                                                  self.lower_threshold_collision_limit,
                                                                                                  self.upper_threshold_collision_limit,)
        # initial_signed_distance = collision_infos[0]
        # normal = collision_infos[1]
        # jacobian = collision_infos[2]
        # normal_times_jacobian = np.matmul(normal.T, jacobian)
        # lower_limit =

        return constraints, lower_limit, upper_limit


    def plan_trajectory(self, group, goal_state, samples, duration, lower_collision_limit=None,
                        upper_collision_limit=None, solver_config=None, collision_check_distance=0.2):
        self.collision_constraints = {}
        self.planning_group = group
        self.planning_samples = samples
        self.lower_threshold_collision_limit = lower_collision_limit
        self.upper_threshold_collision_limit = upper_collision_limit
        self.collision_check_distance = collision_check_distance
        # if (lower_collision_limit is not None or lower_collision_limit != 0) and (upper_collision_limit is not None or upper_collision_limit != 0):
            # self.get_collision_infos(group, lower_collision_limit, upper_collision_limit)
        #
        #     # print self.collision_constraints
        #     # print joint_name, jac_t
        #     # print self.jacobian_by_joint_name
        #     # print np.asarray(self.jacobian_by_joint_name).shape
        # else:
        #     self.logger.debug("ignoring collision constraints . . . . ")
        #
        # status, can_execute_trajectory = self.robot.init_plan_trajectory(group=group,
        #                                                                  current_state=self.get_current_states_for_given_joints(group),
        #                                                                  goal_state=goal_state, samples=int(samples),
        #                                                                  duration=int(duration),
        #                                                                  collision_constraints=self.collision_constraints,
        #                                                                  solver_config=solver_config)
        # return status, can_execute_trajectory
        start_state = self.get_current_states_for_given_joints(group)

        self.robot.init_plan_trajectory(group=group, current_state=self.get_current_states_for_given_joints(group),
                                        goal_state=goal_state, samples=int(samples),
                                        duration=int(duration),
                                        # collision_constraints=self.collision_constraints,
                                        solver_config=solver_config)
        # collision_infos = self.get_collision_infos(self.robot.get_trajectory().initial, group, self.collision_check_distance)

        # self.robot.planner.problem.update_collision_infos(collision_infos)

        status, can_execute_trajectory = self.robot.calulate_trajecotory(self.update_collsion_infos) # callback function

        # status, can_execute_trajectory = self.robot.calulate_trajecotory(None)

        return status, can_execute_trajectory

    def get_current_states_for_given_joints(self, joints):
        current_state = {}
        for joint in joints:
            current_state[joint] = \
            sim.getJointState(bodyUniqueId=self.robot_id, jointIndex=self.joint_name_to_id[joint])[0]
        return current_state

    def execute_trajectory(self, group):
        trajectories = self.robot.get_trajectory()
        sleep_time = trajectories.duration / float(trajectories.no_of_samples)

        for i in range(int(trajectories.no_of_samples)):
            for joint_name, corresponding_trajectory in trajectories.trajectory_by_name.items():
                sim.setJointMotorControl2(bodyIndex=self.robot_id, jointIndex=self.joint_name_to_id[joint_name],
                                          controlMode=sim.POSITION_CONTROL,
                                          targetPosition=corresponding_trajectory[i], targetVelocity=0,
                                          force=self.robot.model.joint_by_name[joint_name].limit.effort,
                                          positionGain=0.03,
                                          velocityGain=.5,
                                          # maxVelocity=float(self.robot.model.joint_by_name[joint_name].limit.velocity)
                                          )
                # self.get_contact_points()
            # time.sleep(trajectories.no_of_samples / float(trajectories.duration))
            # sim.stepSimulation()
            self.step_simulation_for(sleep_time)
            # self.step_simulation_for(0.01)
            # time.sleep(sleep_time)
            # sim.stepSimulation()
        # print trajectories.trajectory
        # for traj in trajectories.trajectory:
        #     for i in range(len(group)):
        #         sim.setJointMotorControl2(bodyIndex=self.robot_id, jointIndex=self.joint_name_to_id[group[i]],
        #                                   controlMode=sim.POSITION_CONTROL,
        #                                   targetPosition=traj[i], targetVelocity=0,
        #                                   force=self.robot.model.joint_by_name[group[i]].limit.effort,
        #                                   positionGain=0.03,
        #                                   velocityGain=.5,
        #                                   # maxVelocity=float(self.robot.model.joint_by_name[joint_name].limit.velocity)
        #                                   )
        #         # self.get_contact_points()
        #     # time.sleep(trajectories.no_of_samples / float(trajectories.duration))
        #     time.sleep(trajectories.duration / float(trajectories.no_of_samples))
        #     # sim.stepSimulation()

        status = "Trajectory execution has finished"
        self.logger.info(status)
        return status

    def plan_and_execute_trajectory(self, group, goal_state, samples, duration, solver_config=None):
        status = "-1"
        status, can_execute_trajectory = self.plan_trajectory(group, goal_state, samples, duration, solver_config=None)
        status += " and "
        status += self.execute_trajectory()

        return status, can_execute_trajectory

    def setup_joint_id_to_joint_name(self):
        for i in range(self.no_of_joints):
            joint_info = sim.getJointInfo(self.robot_id, i)
            self.joint_name_to_id[joint_info[1].decode('UTF-8')] = joint_info[0]

    def reset_joint_states_to(self, trajectory, joints):
        if len(trajectory) == len(joints):
            for i in range(len(trajectory)):
                sim.resetJointState(self.robot_id, self.joint_name_to_id[joints[i]], trajectory[i])
                status = "Reset joints to start pose is complete"

        else:
            status = "cannot reset the joint states as the trajectory and joints size doesn't match"

        # self.logger.info(status)
        return status

    def reset_joint_states(self, joints, motor_dir=None):
        # if motor_dir is None:
        #     # motor_dir = [-1, -1, -1, 1, 1, 1, 1]
        #     motor_dir = np.random.uniform(-1, 1, size=len(joints))
        # half_pi = 1.57079632679
        for joint in joints:
            for j in range(len(joints)):
                sim.resetJointState(self.robot_id, self.joint_name_to_id[joint], joints[joint])
        status = "Reset joints to start pose is complete"
        # self.logger.info(status)
        return status

    def get_joint_states(self, group):
        joint_states = sim.getJointStates(self.robot_id, [self.joint_name_to_id[joint_name] for joint_name in group])
        joint_positions = [state[0] for state in joint_states]
        joint_velocities = [state[1] for state in joint_states]
        joint_torques = [state[3] for state in joint_states]
        return joint_positions, joint_velocities, joint_torques

    def step_simulation_for(self, seconds):
        start = time.time()
        while time.time() < start + seconds:
            sim.stepSimulation(self.gui)

    def get_contact_points(self):
        for i in range(sim.getNumJoints(self.robot_id)):
            contact_points = sim.getClosestPoints(self.robot_id, self.box_id, linkIndexA=i, distance=4)
            contact_points1 = sim.getContactPoints(self.robot_id, self.box_id, linkIndexA=i)

            if len(contact_points) > 0 and len(contact_points1) > 0:
                if contact_points[0][8] < 0:
                    print "index ", i
                    print "positionOnA ", contact_points[0][5]
                    print "positionOnB ", contact_points[0][6]
                    print "contactNormalOnB ", contact_points[0][7]
                    print "contactDistance ", contact_points[0][8]

                if contact_points1[0][8] < 0:
                    print "index 1 ", i
                    print "positionOnA 1 ", contact_points1[0][5]
                    print "positionOnB 1 ", contact_points1[0][6]
                    print "contactNormalOnB 1 ", contact_points1[0][7]
                    print "contactDistance 1 ", contact_points1[0][8]


if __name__ == "__main__":
    sim1 = SimulationWorld()
    sim1.run_simulation()