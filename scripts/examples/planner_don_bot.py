import os
import time
from scripts.TrajectoryOptimizationPlanner.TrajectoryOptimizationPlanner import TrajectoryOptimizationPlanner
import pybullet as p
from random import randint
from collections import OrderedDict

home = os.path.expanduser('~')

class PlannerExample:
    def __init__(self):

        location_prefix = home + "/catkin_ws/src/iai_robots/"

        urdf_file = location_prefix + "iai_donbot_description/robots/don_bot.urdf"
        srdf_file = home + "/catkin_ws/src/iai_robots/iai_donbot_description/ur5_moveit_config/config/ur5.srdf"

        shelf_file = home + "/catkin_ws/src/iai_shelf_description/urdf/shelf.urdf"

        config = {
            "use_gui": True,
            "verbose": "INFO",
            "log_file": True,
            "save_problem": True,
            "robot_config": "robot_config_don_bot.yaml",
            "plot_trajectory": True,
            "db_name": "Trajectory_planner_evaluation"

        }

        self.planner = TrajectoryOptimizationPlanner(**config)
        self.planner.world.toggle_rendering(0)
        self.planner.world.set_gravity(0, 0, -10)
        plane_id = self.planner.add_constraint_from_urdf("plane", "plane.urdf", position=[0, 0, 0.0])
        self.robot_id = self.planner.load_robot(urdf_file,
                                                use_fixed_base=True,
                                                position=[0.6, 0.2, 0],
                                                orientation=p.getQuaternionFromEuler([0, 0, -1.57])
                                                )

        shelf_id = self.planner.add_constraint_from_urdf("shelf", urdf_file=shelf_file, position=[-0.15, 0, 0.0],
                                                         orientation=p.getQuaternionFromEuler([0, 0, 1.57]))

        # table_id = self.planner.add_constraint_from_urdf(urdf_file=location_prefix + "table/table.urdf",
        #                                                  position=[0, 0, 0.0])
        # #
        # self.box_id = self.planner.add_constraint("box1", shape=self.planner.world.BOX, size=[0.05, 0.05, 0.1],
        #                                           position=[-0.15, 0.3, 0.62], mass=100)
        # self.box_id1 = self.planner.add_constraint("box2", shape=self.planner.world.BOX, size=[0.05, 0.05, 0.1],
        #                                           position=[0.0, -0.2, 0.62], mass=100)
        # self.box_id2 = self.planner.add_constraint("box3", shape=self.planner.world.BOX, size=[0.1, 0.05, 0.1],
        #                                           position=[0.0, 0.4, 1], mass=100)

        shelf_item_prefix = home + "/catkin_ws/src/shelf_item_descriptions/urdf/"
        salt_urdf = shelf_item_prefix + "salt.urdf"
        gel_urdf = shelf_item_prefix + "duschGel.urdf"
        gel_id = OrderedDict()

        y, z = 0.3, 1.0
        offset = -0.29
        for x in range(4):
            gel_id[x] = self.planner.add_constraint_from_urdf("gel" + str(x), urdf_file=gel_urdf,
                                                               position=[offset + 0.1 * x, y, z])
            gel_id[x + 4] = self.planner.add_constraint_from_urdf("gel" + str(x), urdf_file=gel_urdf,
                                                               position=[offset + 0.1 * x, y-0.38, z])
        gel_id = OrderedDict()
        y, z = -0.3, 0.62
        offset = -0.29
        for x in range(2):
            gel_id[x] = self.planner.add_constraint_from_urdf("gel" + str(x), urdf_file=gel_urdf,
                                                              position=[offset + 0.1 * x, y, z])
        for x in range(2):
            gel_id[x] = self.planner.add_constraint_from_urdf("gel" + str(x), urdf_file=salt_urdf,
                                                              position=[offset + 0.1 * x, 0.3, z])
        for x in range(1):
            gel_id[x + 4] = self.planner.add_constraint_from_urdf("gel" + str(x + 4), urdf_file=gel_urdf,
                                                                  position=[offset + 0.1 * x, y - 0.14, z])
        lotion_urdf = shelf_item_prefix + "bodyLotion.urdf"
        lotion_id = OrderedDict()
        y, z = -0.4, 1
        offset = -0.14
        for x in range(1):
            lotion_id[x] = self.planner.add_constraint_from_urdf("lotion" + str(x), urdf_file=lotion_urdf,
                                                                 position=[offset + 0.1 * x, y, z])

        self.planner.robot.load_srdf(srdf_file)
        self.planner.world.ignored_collisions = self.planner.robot.get_ignored_collsion()
        self.planner.world.toggle_rendering(1)
        # self.planner.world.step_simulation_for(0.2)

    def run(self):
        start_state = "below_shelf1"
        goal_state = "above_shelf1"

        start_state = "below_shelf"
        goal_state = "above_shelf"
        group = "full_body"

        self.planner.reset_robot_to(start_state, group)

        # goal_state1 = "above_shelf1"
        # group1 = "ur5_arm"

        duration = 10
        samples = 20
        collision_check_distance = 0.15
        collision_safe_distance = 0.1

        _, status, trajectory = self.planner.get_trajectory(samples=samples, duration=duration,
                                                            group=group, goal_state=goal_state,
                                                            # group=group1, goal_state=goal_state1,
                                                            collision_safe_distance=collision_safe_distance,
                                                            collision_check_distance=collision_check_distance)
        print("is trajectory free from collision: ", status)

        if status:
            self.planner.execute_trajectory()


def main():
    example = PlannerExample()
    example.run()


if __name__ == '__main__':
    main()
