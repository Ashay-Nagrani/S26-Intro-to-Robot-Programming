# -*- coding: utf-8 -*-
"""
Lab 3 Pre-Lab
"""

class Robot:
    def __init__(self, ID_number, status, location):
        self.ID_number = ID_number      
        self.status = status            # True = online, False = offline
        self.location = location

    def __str__(self):
        state = "Online" if self.status else "Offline"
        return f"Robot {self.ID_number} | Status: {state} | Location: {self.location}"

    def moveBot(self, new_location):
        """Change the robot's location."""
        self.location = new_location

    def changeStatus(self):
        """Toggle the robot's status."""
        self.status = not self.status


# Create robots
r1 = Robot(101, True, "A3")
r2 = Robot(102, False, "C1")

# Print initial state
print(r1)
print(r2)

# Move robot
r1.moveBot("B4")
print("\nAfter moving r1:")
print(r1)

# Toggle status
r1.changeStatus()
r2.changeStatus()

print("\nAfter toggling status:")
print(r1)
print(r2)
