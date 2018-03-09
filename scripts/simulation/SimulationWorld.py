import logging
import pybullet as sim
import time
import numpy as np
from scripts.interfaces.ISimulationWorldBase import ISimulationWorldBase
from munch import *
import os
import PyKDL as kdl
import itertools
from scripts.utils.utils import Utils as utils
import collections




class SimulationWorld(ISimulationWorldBase):
    def __init__(self, urdf_file=None, use_gui=False, use_real_time_simulation=False, fixed_time_step=0.01):
        self.CYLINDER = sim.GEOM_CYLINDER
        self.BOX = sim.GEOM_BOX

        if urdf_file is None:
            main_logger_name = "Trajectory_Planner"
            verbose = "DEBUG"
            # verbose = False
            self.logger = logging.getLogger(main_logger_name)
            self.setup_logger(main_logger_name, verbose)
        else:
            self.logger = logging.getLogger("Trajectory_Planner."+__name__)

        if use_gui:
            self.gui = sim.connect(sim.GUI)
        else:
            self.gui = sim.connect(sim.DIRECT)


        # self.robot = Robot.Robot(urdf_file)
        self.robot = None
        self.robot_id = -1
        self.joint_name_to_id = {}
        self.start_state_for_traj_planning = {}
        self.end_state_for_traj_planning = {}


        self.planning_group = []
        self.planning_group_ids = []

        self.planning_samples = 0
        self.collision_safe_distance = 0.4
        self.collision_check_distance = 0.2

        self.end_effector_index = 6

        if use_real_time_simulation:
            sim.setRealTimeSimulation(use_real_time_simulation)
        else:
            sim.setTimeStep(fixed_time_step)

        self.no_of_joints = sim.getNumJoints(self.robot_id)
        self.collision_constraints = []

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

    def toggle_rendering(self, enable):
        sim.configureDebugVisualizer(sim.COV_ENABLE_RENDERING, enable)

    def toggle_rendering_while_planning(self, enable=1):
        sim.configureDebugVisualizer(sim.COV_ENABLE_RENDERING, enable)
        sim.configureDebugVisualizer(sim.COV_ENABLE_TINY_RENDERER, enable)
        sim.configureDebugVisualizer(sim.COV_ENABLE_GUI, enable)
        sim.configureDebugVisualizer(sim.COV_ENABLE_SHADOWS, enable)
        sim.configureDebugVisualizer(sim.COV_ENABLE_RGB_BUFFER_PREVIEW, enable)
        sim.configureDebugVisualizer(sim.COV_ENABLE_DEPTH_BUFFER_PREVIEW, enable)
        sim.configureDebugVisualizer(sim.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, enable)

    def set_gravity(self, x=0, y=0, z=-10):
        sim.setGravity(x, y, z)

    def create_constraint(self, shape, mass, position, size=None, radius=None, height=None, orientation=None):
        if position is not None:
            if radius is not None:
                col_id = sim.createCollisionShape(shape, radius=radius, height=height)
                vis_id = sim.createCollisionShape(shape, radius=radius, height=height)
            if size is not None:
                col_id = sim.createCollisionShape(shape, halfExtents=size)
                vis_id = sim.createCollisionShape(shape, halfExtents=size)
            shape_id = sim.createMultiBody(mass, col_id, vis_id, position)

        self.collision_constraints.append(shape_id)

        return shape_id

    def load_urdf(self, urdf_file, position, orientation=None, use_fixed_base=True):

        if orientation is None:
            urdf_id = sim.loadURDF(urdf_file, basePosition=position, useFixedBase=use_fixed_base)
        else:
            urdf_id = sim.loadURDF(urdf_file, basePosition=position,
                                   baseOrientation=orientation, useFixedBase=use_fixed_base)

        return urdf_id

    def set_robot(self, robot):
        if self.robot is None and robot is not None:
            self.robot = robot


    def get_link_states_at(self, trajectory, group):
        link_states = []
        self.reset_joint_states_to(trajectory, group)
        for link_index in self.planning_group_ids:
            state = sim.getLinkState(self.robot_id, link_index, computeLinkVelocity=1,
                                     computeForwardKinematics=1)
            link_states.append(state)
        return link_states

    def extract_ids_from_planning_group(self, group):
        for joint in group:
            self.planning_group_ids.append(self.joint_name_to_id[joint])

    def get_collision_infos(self, initial_trajectory, group, distance=0.10):

        # print initial_trajectory
        collision_infos = self.formulate_collision_infos(initial_trajectory, group, distance)

        return collision_infos

    def get_jacobian_matrix(self, position_jacobian, trajectory_length, planning_group_length, time_step_count):
        jaco1 = np.asarray([[[0] * planning_group_length] * 3] * (time_step_count - 1))
        if len(jaco1):
            jaco1 = np.hstack(jaco1)

        jaco2 = np.asarray(
            [[[0] * planning_group_length] * 3] * (trajectory_length - time_step_count))

        if len(jaco1) > 0 and len(jaco2):
            jaco2 = np.hstack(jaco2)
            jacobian_matrix = np.hstack(
                [jaco1, np.asarray(position_jacobian), jaco2])
        elif len(jaco1) > 0 and len(jaco2) == 0:
            # jacobian_matrix = np.vstack([jaco1, np.asarray(jac_t).reshape(1, 3, 7)])
            jacobian_matrix = np.hstack([jaco1, np.asarray(position_jacobian)])
        elif len(jaco1) == 0 and len(jaco2) > 0:
            jacobian_matrix = np.vstack(
                [np.asarray(position_jacobian).reshape(1, 3, 7), jaco2])
            jacobian_matrix = np.hstack(jacobian_matrix)

        return jacobian_matrix

    def formulate_collision_infos(self, trajectory, group, distance=0.2):

        normal = []
        initial_signed_distance = []
        closest_pts = []

        jacobian_matrix = []
        current_normal_T_times_jacobian = []
        next_normal_T_times_jacobian = []
        start_state = self.get_current_states_for_given_joints(group)
        time_step_count = 0

        for previous_time_step_of_trajectory, current_time_step_of_trajectory, \
            next_time_step_of_trajectory in utils.iterate_with_previous_and_next(trajectory):
            time_step_count += 1

            if next_time_step_of_trajectory is not None:
                current_robot_state = list(current_time_step_of_trajectory)
                next_robot_state = list(next_time_step_of_trajectory)
                zero_vec = [0.0] * len(current_robot_state)
                current_link_states = self.get_link_states_at(current_time_step_of_trajectory, group)
                next_link_states = self.get_link_states_at(next_time_step_of_trajectory, group)

                self.reset_joint_states_to(current_time_step_of_trajectory, group)

                for link_index, current_link_state, next_link_state in itertools.izip(self.planning_group_ids,
                                                                                      current_link_states,
                                                                                      next_link_states):

                    for constraint in self.collision_constraints:

                        cast_closest_points = sim.getConvexSweepClosestPoints(self.robot_id, constraint,
                                                                              linkIndexA=link_index, distance=distance,
                                                                              bodyAfromPosition=current_link_state[0],
                                                                              bodyAfromOrientation=current_link_state[
                                                                                  1],
                                                                              # bodyAfromOrientation=[0, 0, 0, 1],
                                                                              bodyAtoPosition=next_link_state[0],
                                                                              bodyAtoOrientation=next_link_state[1],
                                                                              # bodyAtoOrientation=[0, 0, 0, 1],
                                                                              )


                        if len(cast_closest_points) > 0:

                            closest_pt_on_A_at_t = cast_closest_points[0][5]
                            closest_pt_on_A_at_t_plus_1 = cast_closest_points[0][6]
                            closest_pt_on_B = cast_closest_points[0][7]
                            normal_ = np.vstack(cast_closest_points[0][8]).reshape(3, 1)
                            normal_ = utils.normalize_vector(normal_)
                            dist = cast_closest_points[0][9]
                            fraction = cast_closest_points[0][10]

                            if dist < 0:
                                # print "-----------cast points--------------"
                                # print "A(t)", closest_pt_on_A_at_t
                                # print "A(t+1)", closest_pt_on_A_at_t_plus_1
                                # print "B", closest_pt_on_B
                                # print "normal", normal_.T
                                # print "Distance ", dist
                                # print "fraction ", fraction
                                # print "*************************************"
                                link_state = sim.getLinkState(self.robot_id, link_index, computeLinkVelocity=1,
                                                              computeForwardKinematics=1)
                                current_link_position_in_world_frame = link_state[4]
                                current_link_orentation_in_world_frame = link_state[5]
                                current_closest_point_on_link_in_link_frame = self.get_point_in_local_frame(
                                    current_link_position_in_world_frame, current_link_orentation_in_world_frame,
                                    closest_pt_on_A_at_t)

                                initial_signed_distance.append(dist)
                                closest_pts.append(closest_pt_on_A_at_t)

                                current_position_jacobian, _ = sim.calculateJacobian(self.robot_id, link_index,
                                                                                     # closest_pt_on_A_at_t,
                                                                                     current_closest_point_on_link_in_link_frame,
                                                                                     current_robot_state,
                                                                                     zero_vec, zero_vec)

                                current_state_jacobian_matrix = self.get_jacobian_matrix(current_position_jacobian,
                                                                                         len(trajectory),
                                                                                         len(group),
                                                                                         time_step_count)

                                next_link_position_in_world_frame = next_link_state[4]
                                next_link_orentation_in_world_frame = next_link_state[5]
                                next_closest_point_on_link_in_link_frame = self.get_point_in_local_frame(
                                    next_link_position_in_world_frame, next_link_orentation_in_world_frame,
                                    closest_pt_on_A_at_t_plus_1)

                                next_position_jacobian, _ = sim.calculateJacobian(self.robot_id, link_index,
                                                                                  # closest_pt_on_A_at_t,
                                                                                  next_closest_point_on_link_in_link_frame,
                                                                                  current_robot_state,
                                                                                  zero_vec, zero_vec)

                                next_state_jacobian_matrix = self.get_jacobian_matrix(next_position_jacobian,
                                                                                      len(trajectory),
                                                                                      len(group),
                                                                                      time_step_count + 1)

                                jacobian_matrix.append(current_state_jacobian_matrix)
                                # normal.append(np.asarray(closest_points[0][7]).reshape(3, 1))
                                normal.append(normal_)
                                current_normal_T_times_jacobian.append(np.matmul(normal_.T,
                                                                                 current_state_jacobian_matrix))

                                next_normal_T_times_jacobian.append(np.matmul((1 - fraction) * normal_.T,
                                                                              next_state_jacobian_matrix))


        if len(initial_signed_distance) > 0:
            initial_signed_distance = np.vstack(np.asarray(initial_signed_distance))

        if len(current_normal_T_times_jacobian) > 0:
            current_normal_T_times_jacobian = np.vstack(current_normal_T_times_jacobian)

        if len(next_normal_T_times_jacobian) > 0:
            next_normal_T_times_jacobian = np.vstack(next_normal_T_times_jacobian)

        self.reset_joint_states(start_state)

        return initial_signed_distance, current_normal_T_times_jacobian, next_normal_T_times_jacobian

    def get_point_in_local_frame(self, frame_position, frame_orientation, point):
        # frame = kdl.Frame()
        # print frame_orientation
        rotation = kdl.Rotation.Quaternion(frame_orientation[0], frame_orientation[1], frame_orientation[2],
                                           frame_orientation[3])
        position = kdl.Vector(frame_position[0], frame_position[1], frame_position[2])
        frame = kdl.Frame(rotation, position)
        point = kdl.Vector(point[0], point[1], point[2])

        point_on_frame = frame.Inverse() * point

        return [point_on_frame[0], point_on_frame[1], point_on_frame[2]]

    def update_collsion_infos(self, new_trajectory, delta_trajectory=None):
        trajectory = np.array((np.split(new_trajectory, self.planning_samples)))

        self.robot.planner.trajectory.add_trajectory(trajectory)
        trajectory = np.split(new_trajectory, self.planning_samples)
        collision_infos = self.get_collision_infos(trajectory, self.planning_group,
                                                   distance=self.collision_check_distance)

        constraints, lower_limit, upper_limit = self.robot.planner.problem_model.update_collision_infos(collision_infos,
                                                                                                        self.collision_safe_distance)
        if len(collision_infos[2]) > 0:
            self.robot.planner.update_prob()

        return constraints, lower_limit, upper_limit

    def plan_trajectory(self, group, goal_state, samples, duration, solver_config=None, collision_safe_distance=None,
                        collision_check_distance=0.2):
        # self.collision_constraints = {}
        self.planning_group = group
        self.planning_samples = samples
        self.collision_safe_distance = collision_safe_distance
        self.collision_check_distance = collision_check_distance

        self.extract_ids_from_planning_group(group)
        self.robot.init_plan_trajectory(group=group, current_state=self.get_current_states_for_given_joints(group),
                                        goal_state=goal_state, samples=int(samples),
                                        duration=int(duration),
                                        # collision_constraints=self.collision_constraints,
                                        solver_config=solver_config)
        self.toggle_rendering_while_planning(False)
        status, can_execute_trajectory = self.robot.calulate_trajecotory(self.update_collsion_infos)  # callback function
        self.toggle_rendering_while_planning(True)
        # status, can_execute_trajectory = self.robot.calulate_trajecotory(None)

        return status, can_execute_trajectory

    def get_current_states_for_given_joints(self, joints):
        current_state = {}
        for joint in joints:
            current_state[joint] = \
                sim.getJointState(bodyUniqueId=self.robot_id, jointIndex=self.joint_name_to_id[joint])[0]
        return current_state

    def execute_trajectory(self, trajectory, step_time=None):
        if step_time is None:
            sleep_time = trajectory.duration / float(trajectory.no_of_samples)

        for i in range(int(trajectory.no_of_samples)):
            for joint_name, corresponding_trajectory in trajectory.trajectory_by_name.items():
                sim.setJointMotorControl2(bodyIndex=self.robot_id, jointIndex=self.joint_name_to_id[joint_name],
                                          controlMode=sim.POSITION_CONTROL,
                                          targetPosition=corresponding_trajectory[i], targetVelocity=0,
                                          force=self.robot.model.joint_by_name[joint_name].limit.effort,
                                          positionGain=0.03,
                                          velocityGain=.5,
                                          maxVelocity=float(self.robot.model.joint_by_name[joint_name].limit.velocity)
                                          )

            self.step_simulation_for(sleep_time)

        status = "Trajectory execution has finished"
        self.logger.info(status)
        return status

    def execute_trajectories(self, group, trajectories):
        sleep_time = trajectories.duration / float(trajectories.no_of_samples)

        for i in range(int(trajectories.no_of_samples)):
            for trajectory in trajectories.trajectories:
                for joint_name, corresponding_trajectory in trajectory:
                    sim.setJointMotorControl2(bodyIndex=self.robot_id, jointIndex=self.joint_name_to_id[joint_name],
                                              controlMode=sim.POSITION_CONTROL,
                                              targetPosition=corresponding_trajectory[i], targetVelocity=0,
                                              force=self.robot.model.joint_by_name[joint_name].limit.effort,
                                              positionGain=0.03,
                                              velocityGain=.5,
                                              # maxVelocity=float(self.robot.model.joint_by_name[joint_name].limit.velocity)
                                              )

                self.step_simulation_for(sleep_time)

        status = "Trajectories execution has finished"
        self.logger.info(status)
        return status

    def plan_and_execute_trajectory(self, group, goal_state, samples, duration, solver_config=None,
                                    collision_safe_distance=0.05, collision_check_distance=0.1):
        status = "-1"
        status, can_execute_trajectory = self.plan_trajectory(group, goal_state, samples, duration,
                                                              solver_config=solver_config,
                                                              collision_safe_distance=collision_safe_distance,
                                                              collision_check_distance=collision_check_distance)
        status += " and "
        status += self.execute_trajectory()

        return status, can_execute_trajectory

    def check_for_collision_in_trajectory(self, trajectory, group, collision_safe_distance=0.05):
        collision = False
        start_state = self.get_current_states_for_given_joints(group)

        for previous_time_step_of_trajectory, current_time_step_of_trajectory, \
            next_time_step_of_trajectory in utils.iterate_with_previous_and_next(trajectory):

            if next_time_step_of_trajectory is not None:
                current_link_states = self.get_link_states_at(current_time_step_of_trajectory, group)
                next_link_states = self.get_link_states_at(next_time_step_of_trajectory, group)

                self.reset_joint_states_to(current_time_step_of_trajectory, group)

                for link_index, current_link_state, next_link_state in itertools.izip(self.planning_group_ids,
                                                                                      current_link_states,
                                                                                      next_link_states):

                    for constraint in self.collision_constraints:

                        cast_closest_points = sim.getConvexSweepClosestPoints(self.robot_id, constraint,
                                                                              linkIndexA=link_index,
                                                                              distance=collision_safe_distance,
                                                                              bodyAfromPosition=current_link_state[0],
                                                                              bodyAfromOrientation=current_link_state[
                                                                                  1],
                                                                              # bodyAfromOrientation=[0, 0, 0, 1],
                                                                              bodyAtoPosition=next_link_state[0],
                                                                              bodyAtoOrientation=next_link_state[1],
                                                                              # bodyAtoOrientation=[0, 0, 0, 1],
                                                                              )

                        if len(cast_closest_points) > 0:
                            dist = cast_closest_points[0][9]
                            if dist < 0:
                                collision = True
                                break
                    if collision:
                        break
            if collision:
                break

        self.reset_joint_states(start_state)

        return collision

    def setup_joint_id_to_joint_name(self):
        for i in range(sim.getNumJoints(self.robot_id)):
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

    def reset_joints_to_random_states(self, joints):

        motor_dir = np.random.uniform(-1, 1, size=len(joints))
        half_pi = 1.57079632679
        for joint in joints:
            for j in range(len(joints)):
                sim.resetJointState(self.robot_id, self.joint_name_to_id[joint], motor_dir[j] * half_pi * (-(-1)**j))
        status = "Reset joints to random pose is complete"
        self.logger.info(status)
        return status

    def reset_joint_states(self, joints):
        for joint in joints:
            sim.resetJointState(self.robot_id, self.joint_name_to_id[joint], joints[joint])
        status = "Reset joints to start pose is complete"
        # self.logger.info(status)
        return status

    def reset_objects_to(self, object_id, position=None, orientation=None):
        if position is None:
            position = [0.28, -0.43, 0.98]
        if orientation is None:
            orientation = [0, 0, 0, 1]
        sim.resetBasePositionAndOrientation(object_id, position, orientation)

    def get_joint_states(self, group):
        joint_states = sim.getJointStates(self.robot_id, [self.joint_name_to_id[joint_name] for joint_name in group])
        joint_positions = [state[0] for state in joint_states]
        joint_velocities = [state[1] for state in joint_states]
        joint_torques = [state[3] for state in joint_states]
        return joint_positions, joint_velocities, joint_torques

    def step_simulation_for(self, seconds):
        start = time.time()
        while time.time() < start + seconds:
            sim.stepSimulation()



if __name__ == "__main__":
    sim1 = SimulationWorld()
    sim1.run_simulation()