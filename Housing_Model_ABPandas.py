import abpandas as abp
import random
import copy
import numpy as np
from statistics import median, mean
from tqdm import tqdm
from typing import Union, List
import os
import multiprocessing as mp

python_directory = os.path.dirname(os.path.realpath(__file__))
     

class House(abp.Agent):

    def __init__(self, properties="default"):
        # pass the values to the parent agent
        super().__init__(properties)

        self.my_class = "house"

        if properties == "default":
            self.props = {
                "my_type": None,            # type of house; owned or rented
                "local_realtors": list(),   # the local realtors of the house
                "end_of_life": 0,           # time step when this house will be demolished
                "for_sale?": True,           # whether this house is currently for sale or rent
                "for_rent?": False,          # whether this house is currently for rent
                "date_for_sale": 0,         # when the house was put on the market for sale
                "date_for_rent": 0,         # when the house was put on the market for rent
                "my_owner": None,           # the owner of this house; owner may not be living in the house if it is rented
                "sale_price": 0,            # the price of this house (either now, or when last sold); price sold and rented
                "rent_price": 0,            # the rent price of this house
                "quality": 0,               # index of quality of this house relative to its neighbours
                "my_realtor": None,         # if for sale/rent, which realtor is selling it
                "offered_to": None,         # which household has already made an offer for this house
                "offer_date": 0,            # date of the offer (in ticks)
                "rented_to": None,          # which renter has already made an offer for this house
                "rent_date": 0,             # date of the rent offer (in ticks)
                "my_occupier": None,        # the individual that lives here; can be the owner or the tenant
                "diversity": 0,             # the diversity index of the house (only used for visualisation)
                "G": 0,                     # Getis-Ord z-score for the hotspot analysis
                "attributes": {
                    "rooms": 0,
                    "type": None
                }
            }

class Household(abp.Agent):

    def __init__(self, properties="default"):

        super().__init__(properties)

        self.my_class = "household"

        # create variables here
        if properties == "default":
            self.props = {
                "my_house": None,                           # the house which this household owns/rents
                "income": 0,                                # current income from work per year (this is the ONLY yearly measure)
                "income_rent": list(),                      # income from rent per tick
                "income_surplus": 0,                        # residual income after spending on housing commodities
                "deposit": list(),                          # initial deposit for mortgages         
                "mortgage": list(),                         # value of mortgage - reduces as it is paid off
                "mortgage_initial": list() ,                # value of initial mortgage (does not decrease every tick)
                "mortgage_duration": list(),                # the remaining time on the mortgage 
                "rate": list(),                             # the yearly interest rate of the currently aggreed mortgage
                "rate_duration": list(),                    # the remaining years on the current rate (at the end updates)
                "capital": 0,                               # capital that I have accumulated from selling my house
                "repayment": list(),                        # my mortgage repayment amount, at each tick
                "my_rent": 0,                               # rent at each tick
                "homeless": 0,                              # count of the number of periods that this household has been without a house
                "my_type": None,                            # type of household, 1 for owned and 0 for rented
                "made_offer_on": None,                      # house that this household wants to buy/rent
                "date_of_acquire": 0,                       # when my-house was bought/rented
                "my_ownership": list(),                     # houses I own
                "on_market?": False,                        # currently on the market or not (myType depicts the type of the market I use)
                "on_market_type": None,                     # type of market a buyer is on now
                "propensity": random.uniform(0.0, 1.0),     # the probability I will invest in housing
                "preferences": {
                    "rooms": 0.5,
                    "type": "detached"
                }
            }

class Realtor(abp.Agent):

    def __init__(self, properties="default"):

        super().__init__(properties)

        self.my_class = "realtor"

        if properties == "default":
            self.props = {
                "locality_houses": list(),      # all the houses in the locality
                "records": list(),              # record of transactions
                # {                     
                #     "house": list(),                # record of houses with a transaction(indices match sale_price and rent_price)
                #     "sale_price": list(),           # sale_price of house
                #     "rent_price": list(),           # rent_price of house
                #     "date": list(),                 # date of transaction
                # }
                "mean_price": 0,                # mean_price of all locality houses
                "mean_rent": 0,                 # mean_rent of all locality houses
            }


class HousingModel(abp.Model):

    def __init__(self, space, agents=[], inputs="default"):
        # pass the values to the parent agent
        super().__init__(space, agents)

        # if the user does not provide the model inputs
        if inputs == "default":
            self.inputs = {
                "interest_rate": 3,                 # %
                "max_LTV": 90,                      # %
                "ticks_per_year": 4,                # ticks
                "density": 70,                      # %
                "owned_rent_percentage": 50,        # %
                "initial_occupancy": 95,            # %
                "fully_paid_mortgage_owners": 0,    # %
                "investors": 50,                   # %
                "upgrade_tenancy": 50,               # %
                "house_mean_lifetime": 100,         # years
                "locality": 3,                      # cells
                "affordability": 33,                # % of annual income
                "mortgage_duration": 25,            # years
                "mean_income": 30000,               # £/year
                "capital_mortgage": 100,            # % of income
                "capital_rent": 50,                 # % of income
                "wage_rise": 0,                     # % of income
                "savings": 20,                      # % of surplus income
                "savings_rent": 5,                 # % of surplus income
                "price_difference": 5000,           # £
                "rent_difference": 500,             # £
                "clustering_repeat": 3,             # times
                "max_homeless_period": 5,            # ticks
                "buyer_search_length": 5,           # houses
                "house_construction_rate": 0.36,    # %
                "entry_rate": 4,                    # %
                "exit_rate": 2,                     # %
                "n_realtors": 6,                    # realtors
                "realtor_territory": 16,            # cells (radius)
                "realtor_optimism": 3,              # 
                "realtor_memory": 10,               # ticks or years (requires checking)
                "min_price_percent": 20,            # %
                "price_drop_rate": 3,               # %
                "rent_drop_rate": 3,                # %
                "stamp_duty": False,                # 
                "savings_to_price_threshold": 2,     # 
                "eviction_threshold_mortgage": 3,   # 
                "eviction_threshold_rent": 1,       # 
                "min_rate_duration_M": 2,           # years
                "max_rate_duration_M": 5,           # years
                "min_rate_duration_BTL": 1,         # years
                "max_rate_duration_BTL": 1          # years
            }
        
        # if the user provides the model inputs
        else:
            self.inputs = inputs

        self.monitors = {   
            "medianPriceForSale": 0,            # median Price Of Houses For Sale
            "medianPriceForRent": 0,            # median Price Of Houses For Ren  
            "nUpshocked": 0,                    # total number of upshocked households
            "nDownshocked": 0,                  # total number of downshocked households
            "nUpshockedSell": 0,                # number of households putting their house for sale because their income has risen
            "nDownshockedSell": 0,              # number of households putting their house for sale because their income has dropped
            "nUpshockedRent": 0,                # number of households putting their house for rent because their income has risen
            "nDownshockedRent": 0,              # number of households putting their house for rent because their income has dropped   
            "nDiscouraged": 0,                  # number of households who discouraged by homeless and leave the city
            "nDiscouragedRent": 0,
            "nDiscouragedMortgage": 0,
            "nDiscouragedBTL": 0,
            "nExit": 0,                         # number of households who naturally leave the city or cease to exist
            "nEntry": 0,                        # number of households who naturally enter or born into the city
            "moves": 0,                         # number of households moving in this step
            "nDemolished": 0,                   # number of demolished house  
            "nForceOutSell": 0,                 # number of households whose repayment is greater than income and force to leave
            "nHouseholdsOffered": 0,            # number of households who made an offer on a house (have enough money and have target to buy)
            "meanIncomeForceOutSell": 0,        # cal the mean income of all households who are forced out due to low income to repay mortgage
            "nForceOutRent": 0,                 # number of households whose repayment is greater than income and force to leave
            "meanIncomeForceOutRent": 0,        # cal the mean income of all households who are forced out due to low income to repay mortgage
            "nForceInSell": 0,                  # number of households forced to sell their house
            "meanIncomeForceInSell": 0,         # cal the mean income of all households who are forced to sell their hous 
            "nEvictedMortgage": 0,              # number of evicted households of type mortgage
            "nEvictedRent": 0,                  # number of evicted households of type rent
            "nenterMarketMortgage": 0,          # number of households entering the mortgage market
            "nEnterMarketRent": 0,              # number of households entering the rent market
            "nEnterMarketBuyToLet": 0,          # number of households entering the BTL market
            "nForceSell": 0,                    # number of households forced to put one of their houses on the buy-to-let market
            "meanIncomeEvictedMortgage": 0,     # mean income of evicted households of type mortgage
            "meanIncomeEvictedRent": 0,         # mean income of evicted households of type ren   
            "nEvictedMortgageOneHouse": 0,      # number of evicted households of type mortgage while owning one house
            "nEvictedMortgageMoreHouses": 0,    # number of evicted househoods of type mortgage while owning more than one hous   
            "nHomeless": 0,                     # number of households evicted from their houses (does not include households coming into the system as immigrants
            "nPoorMortgage": 0,                 # number of relatively poor mortgage households
            "nNaturalExit": 0,                  # number of households naturally exiting the system
        }

        # initialise a records variable
        self.records = list()                   # all the records in the system


    def initialise(self):
        """Initialise the model (setup in NetLogo)"""
        # track the phase of the model (at setup or not)
        self.setup = True
        self.ticks = 0
        # calculate the interest per tick
        self.interest_per_tick = self.inputs["interest_rate"] / (self.inputs["ticks_per_year"] * 100)
        # create realtors
        self.initialise_realtors()
        # create houses
        self.initialise_houses()
        # create households and update their surplus income
        self.initialise_households()
        self.setup = False
    
    def initialise_realtors(self):
        """Create realtors"""
        space_centre = self.index_at_ij(max(self.space["i"]) / 2, max(self.space["j"]) / 2)
        space_centre = int(space_centre)
        # find the ring patches within a distance from the centre of the model
        ring_indices = self.indices_in_radius(centre=space_centre, radius=max(self.space["i"]) / 4, outline_only=True)
        self.realtors_indices = list()
        # allocate realtor to the model in a random index in the ring patches
        print(f"Initialising {self.inputs['n_realtors']} realtors")
        for r in tqdm(range(self.inputs["n_realtors"])):
            realtor = Realtor()
            index_realtor = random.choice(ring_indices)
            ring_indices.remove(index_realtor)
            self.realtors_indices.append(index_realtor)
            self.add_agent(realtor, index_realtor)
        
    def initialise_houses(self):
        """Create houses"""
        ## calculate the number of houses and agents
        num_plots = len(self.space.index)
        num_houses = int( (self.inputs["density"] / 100) * num_plots )
        num_houses_m = int( (self.inputs["owned_rent_percentage"] / 100) * num_houses )
        num_houses_r = num_houses - num_houses_m
        num_households = int( (self.inputs["initial_occupancy"] / 100) * num_houses )

        ## define the lifetime distribution for houses
        lifetime_distribution = list(np.random.normal(
            loc=self.inputs["house_mean_lifetime"] * self.inputs["ticks_per_year"], # mean
            scale=200, # standard deviation 
            size=num_houses # sample size
            )) 
        
        # mortgage houses
        print(f"Initialising {num_houses_m} mortgage houses")
        # create empty tracking variables for the mortgage houses
        self.space["mortgage_houses"] = [0 for i in range(len(self.space.index))]
        self.mortgage_houses = list()
        
        for i in tqdm(range(num_houses_m)):
            # create house and assign its my_type to mortgage and its lifetime
            h = House()
            h.props["my_type"] = "mortgage"
            h_life = lifetime_distribution[i]
            lifetime_distribution.remove(h_life)
            h.props["end_of_life"] = int(h_life)
            # find a random patch with no houses
            h_loc_index = random.choice(self.space[self.space["n_agents"] == 0].index)
            h_loc_index = int(h_loc_index)
            # add the house to the model
            self.add_agents(h, h_loc_index)
            self.space.at[h_loc_index, "mortgage_houses"] = h
            self.mortgage_houses.append(h)
            # assign local realtor
            self.assign_local_realtors(h)
            self.record_to_realtor_locality(h)
        
        
        # rent houses
        print(f"Initialising {num_houses_r} rent houses")
        # create empty tracking variables for the rent houses and its lifetime
        self.space["rent_houses"] = [0 for i in range(len(self.space.index))]
        self.rent_houses = list()
        for i in tqdm(range(num_houses_r)):
            # create house and assign its my_type to rent
            h = House()
            h.props["my_type"] = "rent"
            h_life = random.choice(lifetime_distribution)
            lifetime_distribution.remove(h_life)
            h.props["end_of_life"] = int(h_life)
            # find a random patch with no houses
            h_loc_index = random.choice(self.space[self.space["n_agents"] == 0].index)
            h_loc_index = int(h_loc_index)
            # add the house to the model
            self.add_agents(h, h_loc_index)
            self.space.at[h_loc_index, "rent_houses"] = h
            self.rent_houses.append(h)
            # assign local realtor
            self.assign_local_realtors(h)
            self.record_to_realtor_locality(h)
    
    def initialise_households(self):
        n_total = len(self.houses)
        n_mortgage = int(n_total * (self.inputs["owned_rent_percentage"] / 100) * (self.inputs["initial_occupancy"] / 100))
        n_rent = int((n_total - n_mortgage) * (self.inputs["initial_occupancy"] / 100))

        income_distribution = np.random.normal(
            loc=self.inputs["mean_income"], # mean
            scale=self.inputs["mean_income"] / 6, # standard deviation 
            size=n_mortgage) # sample size

        # create households
        print(f"Initialising {n_mortgage} mortgage households")
        self.mortgage_households = list()
        self.space["mortgage_households"] = [0 for i in range(len(self.space.index))]
        for i in tqdm(range(n_mortgage)):
            hh = Household()
            self.add_agent(hh, 0)
            # find all mortgage unoccupied mortgage houses
            temp = self.space[self.space["mortgage_houses"] != 0]
            M_unoccupied_houses_df = temp[temp["n_households"] == 0]
            selected_h = random.choice(list(M_unoccupied_houses_df["houses"]))
            selected_h = selected_h[0]
            # address household props
            hh.props["my_type"] = "mortgage"
            ## manage income and capital (surplus income will be updated at the end of this function)
            hh.props["income"] = income_distribution[i]
            hh.props["income_surplus"] = hh.props["income"] / self.inputs["ticks_per_year"]
            hh.props["capital"] = hh.props["income"] * (self.inputs["capital_mortgage"] / 100)
            ## assure the current house does not provide an income rent
            hh.props["income_rent"].append(0)
            ## address mortgage rate and duration
            hh.props["rate"].append(self.interest_per_tick)
            hh.props["rate_duration"].append(random.randint(self.inputs["min_rate_duration_M"], self.inputs["max_rate_duration_M"]))
            hh.props["mortgage_duration"].append(self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])
            ## address mortgage, repayment and deposit values
            max_repayment = (hh.props["income"] * self.inputs["affordability"]) / (self.inputs["ticks_per_year"] * 100)
            max_mortgage = min([
                (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])) * (max_repayment / self.interest_per_tick),
                (hh.props["capital"] * (self.inputs["max_LTV"] / 100)) / (1 - (self.inputs["max_LTV"] / 100))
            ])
            hh.props["mortgage"].append(max_mortgage)
            hh.props["mortgage_initial"].append(max_mortgage)
            hh.props["repayment"].append( (max_mortgage * self.interest_per_tick / (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"]))) )
            hh.props["deposit"].append( max_mortgage * (100 / self.inputs["max_LTV"] - 1) )

            ## address propensity
            hh.props["propensity"] = random.uniform(0.0, 1.0)
            ## address the ownership and occupancy location of the household
            hh.props["my_ownership"].append(selected_h)
            hh.props["my_house"] = selected_h
            self.move_agent(hh, selected_h.location_index)
            self.mortgage_households.append(hh)
            # address house props
            selected_h.props["my_owner"] = hh
            selected_h.props["my_occupier"] = hh
            selected_h.props["for_sale?"] = False
            selected_h.props["for_rent?"] = False
            selected_h.props["sale_price"] = max_mortgage
            self.record_price(selected_h, record_sale=True)

        income_distribution = np.random.normal(
            loc=self.inputs["mean_income"], # mean
            scale=self.inputs["mean_income"] / 6, # standard deviation 
            size=n_rent # sample size
            ) 
        
        print(f"Initialising {n_rent} rent households")
        self.rent_households = list()
        self.space["rent_households"] = [0 for i in range(len(self.space.index))]
        for i in tqdm(range(n_rent)):
            hh = Household()
            # find all rent unoccupied mortgage houses
            temp = self.space[self.space["rent_houses"] != 0]
            R_unoccupied_houses_df = temp[temp["n_households"] == 0]
            selected_h = random.choice(list(R_unoccupied_houses_df["houses"]))
            selected_h = selected_h[0]
            # address household props
            hh.props["my_type"] = "rent"
            hh.props["my_house"] = selected_h
            ## manage income and capital (surplus income will be updated at the end of this function)
            hh.props["income"] = income_distribution[i]
            hh.props["income_surplus"] = hh.props["income"] / self.inputs["ticks_per_year"]
            hh.props["capital"] = hh.props["income"] * (self.inputs["capital_rent"] / 100)
            ## manage rent
            hh.props["my_rent"] = (hh.props["income"] * self.inputs["affordability"]) / (self.inputs["ticks_per_year"] * 100)
            # address house props
            ## select a random owner
            owner = random.choice(self.mortgage_households)
            ## assign owner and occupier to the house
            selected_h.props["my_owner"] = owner
            selected_h.props["my_occupier"] = hh
            selected_h.props["rented_to"] = hh
            ## assure the house is not for sale or for rent (houses are initialised by default with for_sale? = True)
            selected_h.props["for_sale?"] = False
            selected_h.props["for_rent"] = False
            ## assign a price to the house
            repayment_temp = hh.props["my_rent"]
            selected_h.props["sale_price"] = (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])) * (repayment_temp / self.interest_per_tick)
            selected_h.props["rent_price"] = hh.props["my_rent"]
            self.record_price(selected_h, record_rent=True)
            # address owner props
            owner.props["my_ownership"].append(selected_h)
            owner.props["mortgage"].append(selected_h.props["sale_price"])
            owner.props["mortgage_initial"].append(selected_h.props["sale_price"])
            owner.props["repayment"].append(repayment_temp)
            owner.props["income_rent"].append(selected_h.props["rent_price"])
            owner.props["rate"].append(self.interest_per_tick)
            owner.props["rate_duration"].append(random.randint(self.inputs["min_rate_duration_BTL"], self.inputs["max_rate_duration_BTL"]) * self.inputs["ticks_per_year"])
            owner.props["mortgage_duration"].append(self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])
            ## add the household to the model
            self.add_agent(hh, selected_h.location_index)
            self.rent_households.append(hh)
        
        ## assign owners to houses available on the rent market but not occupied
        # find all unoccupied mortgage houses
        temp = self.space[self.space["rent_houses"] != 0]
        R_unoccupied_houses_df = temp[temp["n_households"] == 0]
        rents = [self.rent_houses[i].props["rent_price"] for i in range(len(self.rent_houses)) if self.rent_houses[i].props["rent_price"] > 0]
        for h in list(R_unoccupied_houses_df["houses"]):
            # select house and owner
            house = h[0]
            owner = random.choice(self.mortgage_households)
            # address owner
            owner.props["my_ownership"].append(house)
            owner.props["mortgage"].append(owner.props["mortgage"][0])
            owner.props["mortgage_initial"].append(owner.props["mortgage_initial"][0])
            owner.props["repayment"].append(owner.props["repayment"][0])
            owner.props["income_rent"].append(0)
            owner.props["rate"].append(self.interest_per_tick)
            owner.props["rate_duration"].append(random.randint(self.inputs["min_rate_duration_BTL"], self.inputs["max_rate_duration_BTL"]) * self.inputs["ticks_per_year"])
            owner.props["mortgage_duration"].append(self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])
            # address house
            house.props["my_owner"] = owner
            house.props["my_occupier"] = None
            house.props["rented_to"] = None
            house.props["sale_price"] = owner.props["my_house"].props["sale_price"]
            house.props["rent_price"] = median(rents)

        ## fully pay for the mortgage of some mortgage households
        if self.inputs["fully_paid_mortgage_owners"] > 0:
            hhs = random.sample(self.mortgage_households, int((self.inputs["fully_paid_mortgage_owners"] / 100) * len(self.rent_households)))
            for hh in hhs:
                for i in range(len(hh.props["my_ownership"])):
                    hh.props["mortgage"][i] = 0
                    hh.props["mortgage_initial"][i] = 0
                    hh.props["mortgage_duration"][i] = None
                    hh.props["repayment"][i] = 0
                    hh.props["rate"][i] = 0
                    hh.props["rate_duration"][i] = None
        
        self.update_surplus_income()
                

    def step(self):
        """Step the model one tick"""
        # update and/or reset global variables and model monitors
        self.update_globals()
        # manage (1) random entry, (2) random exit and (3) discouraged homeless households
        self.manage_population_dynamics()
        # manage the decisions to participate in the market
        self.manage_market_participation()
        # construct new houses (Does not include the reset-empty-houses function from NetLogo)
        self.construct_houses()
        # trade houses
        self.trade_houses()
        # remove outdated records
        self.manage_outdated_records()
        # clear the market from houses not acquired
        self.remove_offers()
        # demolish houses
        self.demolish_houses()
        # decay the prices of houses
        self.decay_prices()
        # update owners parameters (including surplus-income)
        self.update_owners()
        print(f'Finishing step {self.ticks} | n_households = {len(self.households)}, n_houses = {len(self.houses)}, nEvictedRent = {self.monitors["nEvictedRent"]}, nDiscouragedRent = {self.monitors["nDiscouragedRent"]}, nDiscouragedMortgage = {self.monitors["nDiscouragedMortgage"]}, nEnterMortgage = {self.monitors["nEnterMarketMortgage"]}, nEnterBTL = {self.monitors["nEnterMarketBuyToLet"]}, nEnterMarketRent = {self.monitors["nEnterMarketRent"]}')
        print("______________________________________________________")

    ## main step functions
    def update_globals(self):
        self.ticks += 1
        self.interest_per_tick = self.inputs["interest_rate"] / (self.inputs["ticks_per_year"] * 100)
        self.monitors["nDiscouraged"] = 0 
        self.monitors["nDiscouragedRent"] = 0 
        self.monitors["nDiscouragedMortgage"] = 0 
        for realtor in self.realtors:
            prices_locality = [h.props["sale_price"] for h in realtor.props["locality_houses"] if h.props["sale_price"] > 0]
            rents_locality = [h.props["rent_price"] for h in realtor.props["locality_houses"] if h.props["rent_price"] > 0]
            if len(prices_locality) > 0: realtor.props["mean_price"] = mean(prices_locality)
            if len(rents_locality) > 0: realtor.props["mean_rent"] = mean(rents_locality)

    def manage_population_dynamics(self):
        """Manage random entry and exit of households"""
        # Exit
        n_exit = int(len(self.households) * (self.inputs["exit_rate"] / 100))
        # find all the households occupying a house
        occupying_hhs = [hh for hh in self.households if hh.props["my_house"] is not None]
        # select a random set of households to exit (make sure the sample selected is not larger than the number of households occupying houses)
        exiting_hhs = random.sample(occupying_hhs, min([n_exit, len(occupying_hhs)]) )
        # iterate through the exiting households
        for hh in exiting_hhs:
            # assure the agent has a house to evict from
            ## cases where an mortgage households is evicted lead to a chain of evictions of rent households (where their "my_house" is set to None)
            ## if one of the rent households happens to be randomly selected to exit, it causes an error as "my_house" is None
            if hh.props["my_house"] is not None:
                self.evict(hh)
            self.remove_agent(hh)
        # monitor the number of households randomly exiting the system
        self.monitors["nNaturalExit"] = len(exiting_hhs)
        
        # Entry
        n_enter = int(len(self.households) * (self.inputs["entry_rate"] / 100))
        # generate a normal distribution for the entering households 
        income_distribution = np.random.normal(
            loc=self.inputs["mean_income"], # mean
            scale=self.inputs["mean_income"] / 6, # standard deviation 
            size=n_enter) # sample size
        types = ["rent", "mortgage"]
        for i in range(n_enter):
            hh = Household()
            my_type = random.choice(types)
            hh.props["my_type"] = my_type
            self.enter_market(hh, my_type)
            ## manage income and capital
            hh.props["income"] = income_distribution[i]
            hh.props["income_surplus"] = hh.props["income"] / self.inputs["ticks_per_year"]
            hh.props["capital"] = hh.props["income"] * (self.inputs[f"capital_{my_type}"] / 100)
            ## add the agent to the model
            self.add_agent(hh)

        # Homeless
        homeless_hhs = [hhh for hhh in self.households if hhh.props["my_house"] is None]
        self.homeless_R_hhs = list()
        for hh in homeless_hhs:
            hh.props["homeless"] += 1
            if hh.props["homeless"] > self.inputs["max_homeless_period"]:
                self.monitors["nDiscouraged"] += 1
                if hh.props["on_market_type"] == "mortgage": self.monitors["nDiscouragedMortgage"] += 1
                if hh.props["on_market_type"] == "buy-to-let": self.monitors["nDiscouragedBTL"] += 1
                if hh.props["on_market_type"] == "rent": 
                    self.monitors["nDiscouragedRent"] += 1
                    self.homeless_R_hhs.append(hh)
                self.remove_agent(hh)
        
    def manage_market_participation(self):
        occupying_hhs = [hh for hh in self.households if hh.props["my_house"] is not None]
        # relatively poor households with my_type = mortgage
        poor_mortgage = [
            hh for hh in occupying_hhs \
            if hh.props["on_market?"] == False \
            and hh.props["my_type"] == "mortgage" \
            and (sum(hh.props["repayment"]) * self.inputs["ticks_per_year"]) > (self.inputs["eviction_threshold_mortgage"] * (hh.props["income"] + (sum(hh.props["income_rent"]) * self.inputs["ticks_per_year"])) * (self.inputs["affordability"] / 100)) 
            ]
        # relatively poor mortgage households and only one house (these will be evicted)
        poor_mortgage_evict = [hh for hh in poor_mortgage if len(hh.props["my_ownership"]) <= 1]
        # relatively poor rent households (these will always be evicted)
        poor_rent = [
            hh for hh in occupying_hhs \
            if hh.props["on_market?"] == False \
            and hh.props["my_type"] == "rent" \
            and (hh.props["my_rent"] * self.inputs["ticks_per_year"]) > (self.inputs["eviction_threshold_rent"] * hh.props["income"] * self.inputs["affordability"] / 100)
            ]
        # all relatively poor rent households with my_type = rent are to be evicted
        poor_rent_evict = poor_rent
        # union of all the households to be evicted
        poor_evict = poor_mortgage_evict + poor_rent_evict

        # iterate through all the households to be evicted
        for hh in poor_evict:
            self.evict(hh)
            self.enter_market(hh, "rent")
        
        # relatively poor mortgage households with more than one house and without a house already on sale
        ## these will stay and will be forced to sell one house
        ## if a house is on sale, then this owner is waiting for the sale to happen to make profit and stop being poor 
        poor_mortgage_stay = [
            hh for hh in poor_mortgage \
            if len(hh.props["my_ownership"]) > 1 \
            and len([h for h in hh.props["my_ownership"] if h.props["for_sale?"] == True or h.props["for_rent?"] == True] ) == 0 \
            ]

        for hh in poor_mortgage_stay:
            self.force_sell(hh)
        
        # relatively rich mortgage households
        rich_mortgage = [
            hh for hh in occupying_hhs \
            if hh.props["my_type"] == "mortgage" \
            and hh.props["on_market?"] == False \
            and hh.props["capital"] > median(hh.props["mortgage"]) * (1 - (self.inputs["max_LTV"] / 100)) \
            and ((hh.props["income"] + (sum(hh.props["income_rent"]) * self.inputs["ticks_per_year"])) - (sum(hh.props["repayment"]) * self.inputs["ticks_per_year"])) * (self.inputs["affordability"] / 100) > median(hh.props["repayment"]) * self.inputs["ticks_per_year"]
        ]
        # relatively rich rent households
        rich_rent = [
            hh for hh in occupying_hhs \
            if hh.props["my_type"] == "rent" \
            and hh.props["on_market?"] == False \
            and hh.props["capital"] > (self.inputs["savings_to_price_threshold"] * hh.props["my_house"].props["sale_price"] * (1 - (self.inputs["max_LTV"] / 100))) \
            and hh.props["income"] * (self.inputs["affordability"] / 100) > hh.props["my_house"].props["sale_price"] * (self.inputs["max_LTV"] / 100) * self.interest_per_tick / (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"]))
        ]
        # assure no household is considered both poor and rich (only occurs due to user input errors)
        rich_mortgage = list(set(rich_mortgage) - set(poor_mortgage))
        rich_rent = list(set(rich_rent) - set(poor_rent))

        for hh in rich_mortgage:
            if hh.props["propensity"] >= 1 - (self.inputs["investors"] / 100):
                self.enter_market(hh, "buy-to-let")
        
        rich_rent_rent = list()
        for hh in rich_rent:
            if hh.props["propensity"] >= 1 - (self.inputs["upgrade_tenancy"] / 100):
                self.enter_market(hh, "rent")
                rich_rent_rent.append(hh)
            else:
                self.enter_market(hh, "mortgage")
        
        # manage globals
        self.monitors["nPoorMortgage"] = len(poor_mortgage)
        self.monitors["nEvictedMortgage"] = len(poor_mortgage_evict)
        self.monitors["nEnterMarketRent"] = len(poor_evict) + len(rich_rent_rent)
        self.monitors["nHomeless"] = len(poor_evict)
        self.monitors["nEnterMarketMortgage"] = len(rich_rent)
        self.monitors["nEnterMarketBuyToLet"] = len(rich_mortgage)
        self.monitors["nForceSell"] = len(poor_mortgage_stay)
        self.monitors["nEvictedRent"] = len(poor_rent_evict)
        if len(poor_mortgage_evict) > 0:
            self.monitors["meanIncomeEvictedMortgage"] = mean([hh.props["income"] for hh in poor_mortgage_evict])
        else:
            self.monitors["meanIncomeEvictedMortgage"] = 0
        if len(poor_rent_evict) > 0:
            self.monitors["meanIncomeEvictedRent"] = mean([hh.props["income"] for hh in poor_rent_evict])
        else:
            self.monitors["meanIncomeEvictedRent"] = 0

    def construct_houses(self):
        n_construct = int(len(self.houses) * (self.inputs["house_construction_rate"] / 100))
        lifetime_distribution = list(np.random.normal(
            loc=(self.inputs["house_mean_lifetime"] * self.inputs["ticks_per_year"]) + self.ticks, # mean
            scale=200, # standard deviation 
            size=n_construct # sample size
        ))
        # construct a number of new houses
        self.constructed_houses = list()
        for i in range(n_construct):
            # find the current vacant plorts
            vacant_plots = self.space[self.space["n_houses"] == 0]
            
            # if there are any vacant plots, randomly choose a vacant plot and construct the house
            if len(vacant_plots) > 0:
                # find a vacant plot index
                vacant_i = random.choice(vacant_plots.index)
                # create house, define its type and its lifetime
                house = House()
                house.props["my_type"] = "mortgage"
                house_life = lifetime_distribution[i]
                house.props["end_of_life"] = int(house_life)
                # add the house to the model
                self.add_agent(house, vacant_i)
                self.put_on_market(house)
                # assign local realtor
                self.assign_local_realtors(house)
                self.record_to_realtor_locality(house)
                self.constructed_houses.append(house)
            else:
                break

    def trade_houses(self):
        houses_for_sale = [h for h in self.houses if h.props["for_sale?"] == True]
        houses_for_rent = [h for h in self.houses if h.props["for_rent?"] == True]

        houses_for_sale_new = [h for h in houses_for_sale if h.props["date_for_sale"] == self.ticks]
        houses_for_rent_new = [h for h in houses_for_rent if h.props["date_for_rent"] == self.ticks]
        
        # value houses newly added to the market
        for house in houses_for_sale_new:
            house.props["sale_price"] = max(self.evaluate(house))
        for house in houses_for_rent_new:
            house.props["rent_price"] = max(self.evaluate(house))

        prices_on_market = [h.props["sale_price"] for h in houses_for_sale]
        rents_on_market = [h.props["rent_price"] for h in houses_for_rent]
        if len(prices_on_market) > 0: 
            self.monitors["medianPriceForSale"] = median(prices_on_market)
        else:
            self.monitors["medianPriceForSale"] = 0
        if len(rents_on_market) > 0:
            self.monitors["medianPriceForRent"] = median(rents_on_market)
        else:
            self.monitors["medianPriceForRent"] = 0

        # make offers
        buyers = [hh for hh in self.households if hh.props["on_market?"] == True]
        buyers_mortgage = [b for b in buyers if b.props["on_market_type"] == "mortgage"]
        buyers_BTL = [b for b in buyers if b.props["on_market_type"] == "buy-to-let"]
        buyers_rent = [b for b in buyers if b.props["on_market_type"] == "rent"]

        for buyer in buyers:
            # make offer mortgage
            if buyer.props["on_market_type"] == "mortgage":
                
                # make-offer-mortgage
                new_repayment = (buyer.props["income"] * self.inputs["affordability"]) / (self.inputs["ticks_per_year"] * 100)
                new_mortgage = (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])) * (new_repayment / self.interest_per_tick)
                budget = new_mortgage
                deposit = buyer.props["capital"]
                current_house = buyer.props["my_house"]
                current_ownership = buyer.props["my_ownership"]

                # if the buyer owns a house, update the deposit to be capital + sale_price of the owned house
                if current_house is not None and len(current_ownership) > 0:
                    i = current_ownership.index(current_house)
                    if current_house.props["for_sale?"] == True:
                        deposit += (current_house.props["sale_price"] - buyer.props["mortgage"][i])
                
                # update upper bound and stop if it is 0 or less
                upperbound = budget + deposit
                if self.inputs["max_LTV"] < 100:
                    upperbound = min([
                        budget + deposit,
                        deposit / (1 - (self.inputs["max_LTV"] / 100))
                    ])
                
                if upperbound <= 0:
                    if current_house is not None:
                        self.leave_market(buyer)
                        self.remove_from_market(current_house)
                    continue
                
                # calculate lowerbound
                lowerbound = upperbound * 0.7

                # find all the interesting houses
                interesting_houses = [
                    h for h in houses_for_sale \
                    if h.props["offered_to"] is None \
                    and h.props["sale_price"] <= upperbound \
                    and h.props["sale_price"] > lowerbound \
                    and h != current_house \
                    and h not in current_ownership
                    ]
                # apply bounded rationality
                if len(interesting_houses) > self.inputs["buyer_search_length"]:
                    interesting_houses = random.sample(interesting_houses, self.inputs["buyer_search_length"])

                # select a house and make an offer
                if len(interesting_houses) > 0:
                    prices = [h.props["sale_price"] for h in interesting_houses]
                    selected_price = max(prices)
                    i = prices.index(selected_price)
                    selected_h = interesting_houses[i]
                    selected_h.props["offered_to"] = buyer
                    selected_h.props["offer_date"] = self.ticks
                    buyer.props["made_offer_on"] = selected_h

            # make offer buy-to-let
            if buyer.props["on_market_type"] == "buy-to-let":
                new_repayment = (buyer.props["income"] * self.inputs["affordability"]) / (self.inputs["ticks_per_year"] * 100)
                new_mortgage = (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])) * (new_repayment / self.interest_per_tick)
                budget = new_mortgage
                deposit = buyer.props["capital"]
                current_house = buyer.props["my_house"]
                current_ownership = buyer.props["my_ownership"]

                # update upper bound and stop if it is 0 or less
                upperbound = budget + deposit
                if self.inputs["max_LTV"] < 100:
                    upperbound = min([
                        budget + deposit,
                        deposit / (1 - (self.inputs["max_LTV"] / 100))
                    ])
                
                if upperbound <= 0:
                    self.leave_market(buyer)
                    continue
                
                # calculate lowerbound
                lowerbound = upperbound * 0.7

                # find all the interesting houses
                interesting_houses = [
                    h for h in houses_for_sale \
                    if h.props["offered_to"] is None \
                    and h.props["sale_price"] <= upperbound \
                    and h.props["sale_price"] > lowerbound \
                    and h != current_house \
                    and h not in current_ownership
                    ]
                # apply bounded rationality
                if len(interesting_houses) > self.inputs["buyer_search_length"]:
                    interesting_houses = random.sample(interesting_houses, self.inputs["buyer_search_length"])

                # select a house and make an offer
                if len(interesting_houses) > 0:
                    prices = [h.props["sale_price"] for h in interesting_houses]
                    selected_price = max(prices)
                    i = prices.index(selected_price)
                    selected_h = interesting_houses[i]
                    selected_h.props["offered_to"] = buyer
                    selected_h.props["offer_date"] = self.ticks
                    buyer.props["made_offer_on"] = selected_h

            # make offer rent
            if buyer.props["on_market_type"] == "rent":
                
                # make-offer-rent
                new_rent = (buyer.props["income"] * self.inputs["affordability"]) / (self.inputs["ticks_per_year"] * 100)
                budget = new_rent
                upperbound = budget
                lowerbound = upperbound * 0.7
                current_house = buyer.props["my_house"]
                # find all the interesting houses
                interesting_houses = [
                    h for h in houses_for_rent \
                    if h.props["offered_to"] is None \
                    and h.props["rent_price"] <= upperbound \
                    and h.props["rent_price"] > lowerbound \
                    and h != current_house
                    ]
                # apply bounded rationality
                if len(interesting_houses) > self.inputs["buyer_search_length"]:
                    interesting_houses = random.sample(interesting_houses, self.inputs["buyer_search_length"])
                
                # select a house and make an offer
                if len(interesting_houses) > 0:
                    prices = [h.props["rent_price"] for h in interesting_houses]
                    selected_price = max(prices)
                    i = prices.index(selected_price)
                    selected_h = interesting_houses[i]
                    selected_h.props["offered_to"] = buyer
                    selected_h.props["offer_date"] = self.ticks
                    buyer.props["made_offer_on"] = selected_h
            
        # find all buyers making an offer
        offering_buyers = [
            b for b in buyers \
            if b.props["made_offer_on"] is not None
        ]

        # if the chain is True, make a transaction
        for hh in offering_buyers:
            if self.follow_chain(hh, hh) == True:
                # define the house to move to
                new_house = hh.props["made_offer_on"]

                # buyers on buy-to-let and mortgage market make a transaction
                if hh.props["on_market_type"] == "mortgage" or hh.props["on_market_type"] == "buy-to-let":
                    buyer = hh
                    seller = new_house.props["my_owner"]
                    # manage the surplus of the surplus if it exists
                    if seller is not None: self.manage_surplus_seller(seller, new_house)
                    self.manage_surplus_buyer(buyer)
                    self.manage_ownership_buyer(buyer)
                    if seller is not None: self.manage_ownership_seller(seller, new_house)

                # buyers on a rent market make a transaction
                if hh.props["on_market_type"] == "rent":
                    tenant = hh
                    landlord = new_house.props["my_owner"]
                    self.manage_surplus_landlord(landlord, new_house)
                    self.manage_surplus_tenant(tenant)
                    self.manage_ownership_tenant(tenant)

    def manage_outdated_records(self):
        # loop through all the realtors
        for realtor in self.realtors:
            # loop through all the records of the realtor
            for record in realtor.props["records"]:
                # if the record is too old, remove it from the list
                if record["date"] < self.ticks - self.inputs["realtor_memory"]:
                    realtor.props["records"].remove(record)
    
    def remove_offers(self):
        # find all the houses still on the market
        houses_on_market = [h for h in self.houses if h.props["for_sale?"] == True or h.props["for_rent?"] == True]
        # remove the houses from the market
        for house in houses_on_market:
            if house.props["offered_to"] is not None: house.props["offered_to"].props["made_offer_on"] = None
            house.props["offered_to"] = None
            house.props["offer_date"] = 0

    def demolish_houses(self):
        self.monitors["nDemolished"] = 0
        
        # find the minimum rent and sale prices of houses on the market
        min_sale_price = self.monitors["medianPriceForSale"] * (self.inputs["min_price_percent"] / 100)
        min_rent_price = self.monitors["medianPriceForRent"] * (self.inputs["min_price_percent"] / 100)

        # find all the mortgage and rent houses to be demolished
        mortgage_houses_demolish = [
            h for h in self.houses \
            if h.props["my_type"] == "mortgage" \
            and (self.ticks > h.props["end_of_life"] or (h.props["for_sale?"] == True and h.props["sale_price"] < min_sale_price))
        ]
        rent_houses_demolish = [
            h for h in self.houses \
            if h.props["my_type"] == "rent" \
            and (self.ticks > h.props["end_of_life"] or (h.props["for_rent?"] == True and h.props["rent_price"] < min_rent_price))
        ]
        self.m_endOfLife = [
            h for h in self.houses \
            if h.props["my_type"] == "mortgage"
            and self.ticks > h.props["end_of_life"]
        ]
        self.m_cheap = [
            h for h in self.houses \
            if h.props["my_type"] == "mortgage" \
            and (h.props["for_sale?"] == True and h.props["sale_price"] < min_sale_price)
        ]
        self.r_endOfLife = [
            h for h in self.houses \
            if h.props["my_type"] == "rent"
            and self.ticks > h.props["end_of_life"]
        ]
        self.r_cheap = [
            h for h in self.houses \
            if h.props["my_type"] == "rent" \
            and (h.props["for_rent?"] == True and h.props["rent_price"] < min_rent_price)
        ]

        # count the demolished houses
        self.monitors["nDemolished"] = len(mortgage_houses_demolish) + len(rent_houses_demolish)

         # demolish the rent houses
        for house in rent_houses_demolish:
            self.remove_record(house)
            owner = house.props["my_owner"]
            occupier = house.props["my_occupier"]
            # if there is an occupier (i.e., tenant)
            if occupier is not None:
                self.evict(occupier)
                self.enter_market(occupier, "rent")
            # add the sale price to the capital of the owner after deducing the mortgage
            i = owner.props["my_ownership"].index(house)
            owner.props["capital"] = max([
                (owner.props["capital"] + house.props["sale_price"] - owner.props["mortgage"][i]),
                0
            ])
            # remove any offers made on the house
            if house.props["offered_to"] is not None: house.props["offered_to"].props["made_offer_on"] = None
            # manage the owner parameters
            del owner.props["my_ownership"][i]
            del owner.props["mortgage"][i]
            del owner.props["mortgage_initial"][i]
            del owner.props["mortgage_duration"][i]
            del owner.props["repayment"][i]
            del owner.props["income_rent"][i]
            del owner.props["rate"][i]
            del owner.props["rate_duration"][i]
            # remove the house from the model (demolish it)
            self.remove_agent(house)
            

        # demolish the mortgage houses
        for house in mortgage_houses_demolish:
            self.remove_record(house)
            owner = house.props["my_owner"]
            occupier = house.props["my_occupier"]
            # if the house is for mortgage and not for sale (i.e., the owner should be the occupier of the house)
            if house.props["for_sale?"] == False:
                ### increase capital after deducing the mortgage from the sale price of the house (mortgage not considered in NetLogo)
                i = owner.props["my_ownership"].index(house)
                owner.props["capital"] = max([
                    (owner.props["capital"] + house.props["sale_price"] - owner.props["mortgage"][i]),
                    0
                ])
                self.evict(occupier)
                self.enter_market(occupier, "mortgage")
            # if the house is for mortgage and for sale; i.e., there are two options: 
            ## (1) the owner put offered a previous rent house on the market as a type mortgage; 
            ## (2) the owner put his/her own my-house on the market
            if house.props["for_sale?"] == True or house.props["for_rent?"] == True:
                ### if the house is offered to an agent (safe gaurd; should not happen as the market was cleared from houses before this step)
                if house.props["offered_to"] is not None: 
                    house.props["offered_to"].props["made_offer_on"] = None
                if house.props["my_occupier"] is not None and house.props["my_owner"] is not None:
                    i = owner.props["my_ownership"].index(house)
                    owner.props["capital"] = max([
                        (owner.props["capital"] + house.props["sale_price"] - owner.props["mortgage"][i]),
                        0
                    ])
                    self.evict(occupier)
                    self.enter_market(occupier, "mortgage")
            # if the house has an owner but there is nobody occupying it (can happen if it was for rent and is now put on the mortgage market by a relatively poor household)
            if owner is not None and occupier is None:
                i = owner.props["my_ownership"].index(house)
                del owner.props["my_ownership"][i]
                del owner.props["mortgage"][i]
                del owner.props["mortgage_initial"][i]
                del owner.props["mortgage_duration"][i]
                del owner.props["repayment"][i]
                del owner.props["income_rent"][i]
                del owner.props["rate"][i]
                del owner.props["rate_duration"][i]
            # remove the agent from the model
            self.remove_agent(house)
            
    def decay_prices(self):
        houses_on_market = [
            h for h in self.houses \
            if (h.props["for_sale?"] == True and h.props["my_type"] == "mortgage") \
            or (h.props["for_rent?"] == True and h.props["my_type"] == "rent")
        ]
        for house in houses_on_market:
            house.props["sale_price"] = house.props["sale_price"] * (1 - (self.inputs["price_drop_rate"] / 100))
            house.props["rent_price"] = house.props["rent_price"] * (1 - (self.inputs["rent_drop_rate"] / 100))

    def update_owners(self):
        
        owners = [
            hh for hh in self.households \
            if len(hh.props["my_ownership"]) > 0
        ]

        for owner in owners:
            for i in range(len(owner.props["my_ownership"])):
                owner.props["mortgage"][i] -= owner.props["repayment"][i]
                if owner.props["mortgage"][i] <= 0:
                    owner.props["mortgage"][i] = 0
                    owner.props["repayment"][i] = 0
                owner.props["capital"] += owner.props["income_surplus"] * (self.inputs["savings"] / 100)

                # address rate duration
                ## if the fixed-rate agreement term ends and the household still has repayments
                if owner.props["rate_duration"][i] == 0 and owner.props["repayment"][i] > 0:
                    # if there is a new rate, calculate new repayment
                    if owner.props["rate"][i] != self.interest_per_tick:
                        total_mortgage = owner.props["mortgage_initial"][i]
                        new_repayment = (total_mortgage * self.interest_per_tick) / (1- (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticke_per_year"]))
                        owner.props["repayment"][i] = new_repayment
                    owner.props["rate"][i] = self.interest_per_tick
                    # if this is the owner's home
                    if i == 0:
                        owner.props["rate_duration"][i] = random.randint(self.inputs["min_rate_duration_M"], self.inputs["max_rate_duration_M"])
                    else:
                        owner.props["rate_duration"][i] = random.randint(self.inputs["min_rate_duration_BTL"], self.inputs["max_rate_duration_BTL"])
                    # subtract 1 tick from the rate duration and mortgage duration
                    if owner.props["rate_duration"][i] is not None: owner.props["rate_duration"][i] -= 1
                    if owner.props["mortgage_duration"][i] is not None: owner.props["mortgage_duration"][i] -= 1
            self.update_income(owner)

        # manage non owners (can be tenants and households on the rent or mortgage market)
        non_owners = [
            hh for hh in self.households \
            if len(hh.props["my_ownership"]) == 0
        ]

        for hh in non_owners:
            hh.props["capital"] += hh.props["income_surplus"] * (self.inputs["savings_rent"] / 100)
            self.update_income(hh)


    ## functions called within the main initialisation fucntions (and occasionally in step fucntions)
    def update_surplus_income(self):
        for hh in self.households:
            self.update_income(hh)

    def update_income(self, household:Household):
        hh = household
        hh.props["income_surplus"] = (hh.props["income"] / self.inputs["ticks_per_year"]) + sum(hh.props["income_rent"]) - sum(hh.props["repayment"]) - hh.props["my_rent"]

        if self.setup == False:
            hh.props["income"] = hh.props["income"] * (1 + (self.inputs["wage_rise"] / 100))



    ## functions called within the main step functions only    
    def evict(self, agent:Union[Household, List[Household]]):
        """
        Evict an agent object
        
        Parameters
        ----------
        agent: Household object or a list of Household objects
        """
        # if the agent is of type "mortgage" (implies that the house is also "mortgage")
        if agent.props["my_type"] == "mortgage":
            # manage the house to be evicted
            my_house = agent.props["my_house"]
            my_house.props["my_occupier"] = None
            my_house.props["my_owner"] = None
            my_house.props["rented_to"] = None
            self.put_on_market(my_house)
            # iterate through all the houses except my_house
            for house in agent.props["my_ownership"]:
                if house != my_house:
                    # if my owned house is for rent
                    if house.props["my_type"] == "rent":
                        # if the house is occupied, evict the occupier
                        if house.props["my_occupier"] is not None:
                            occupier = house.props["my_occupier"]
                            self.evict(occupier)
                            self.enter_market(occupier, "rent")
                        # manage house props and put it on the market
                        house.props["my_type"] = "mortgage"
                        house.props["my_occupier"] = None
                        house.props["my_owner"] = None
                        house.props["rented_to"] = None
                        house.props["offered_to"] = None
                        self.put_on_market(house)
                    # if my owned house is of type mortgage (implies it is unoccupied)
                    if house.props["my_type"] == "mortgage":
                        # manage house props
                        house.props["my_occupier"] = None
                        house.props["my_owner"] = None
                        house.props["rented_to"] = None
                        house.props["offered_to"] = None
                        self.put_on_market(house)
            # assure the owner being evicted now has no house and no ownership
            agent.props["my_house"] = None
            agent.props["my_ownership"] = list()
            agent.props["mortgage"] = list()
            agent.props["repayment"] = list()
            agent.props["income_rent"] = list()
            agent.props["my_rent"] = 0
            agent.props["homeless"] = 0
            return True
        
        # if the agent is of type "rent" (implies the house is also of type "rent")
        if agent.props["my_type"] == "rent":
            # manage the house (put it back on the rent market)
            house = agent.props["my_house"]
            house.props["my_occupier"] = None
            house.props["rented_to"] = None
            house.props["offered_to"] = None
            self.put_on_market(house)
            # assue the landlord decreases their income_rent due to the eviction of a tenant
            landlord = house.props["my_owner"]
            if landlord is not None:
                house_i = landlord.props["my_ownership"].index(house)
                landlord.props["income_rent"][house_i] = 0
            # manage the original evicted household (tenant) props
            agent.props["my_house"] = None
            agent.props["my_rent"] = 0
            agent.props["homeless"] = 0
            return True

    def put_on_market(self, house:House):
        """
        Put one house on the market
        
        Parameters
        ----------
        house: House object
        """
        if house.props["my_type"] == "mortgage":
            house.props["for_sale?"] = True
            house.props["for_rent?"] = False
            house.props["offered_to"] = None
            house.props["date_for_sale"] = self.ticks
        elif house.props["my_type"] == "rent":
            house.props["for_sale?"] = False
            house.props["for_rent?"] = True
            house.props["offered_to"] = None
            house.props["date_for_rent"] = self.ticks
    
    def remove_from_market(self, house:House):
        """
        Remove one house from the market

        Parameters
        ----------
        house: House object
        """
        house.props["for_sale?"] = False
        house.props["for_rent?"] = False
        if house.props["offered_to"] is not None:
            house.props["offered_to"].props["made_offer_on"] = None
        house.props["offered_to"] = None
        house.props["rented_to"] = None
        house.props["offer_date"] = 0

    def enter_market(self, household:Household, market:str):
        """
        Place a household on the housing market
        
        Parameters
        ----------
        household: Household agent
        market: Market string ("mortgage" or "rent")
        """
        household.props["on_market?"] = True
        household.props["on_market_type"] = market

    def leave_market(self, household:Household, market:str):
        """
        Remove a household from the housing market
        
        Parameters
        ----------
        household: Household agent
        """
        household.props["on_market?"] = False
        household.props["on_market_type"] = None

    def force_sell(self, household:Household):
        """
        Force a household to put one of their ownership on the market

        Parameters
        ----------
        agent: Household agent
        """
        hh = household
        # find the ownership excluding my house
        my_ownership_b = [h for h in hh.props["my_ownership"] if h != hh.props["my_house"]]
        # find the ownership that is vacant (not rented)
        my_ownership_not_rented = [h for h in my_ownership_b if h.props["my_type"] == "rent" and h.props["my_occupier"] is None]
        # if there is any non rented houses, select one of them to sell (no need to evict an owner)
        if len(my_ownership_not_rented) > 0:
            h_to_sell = random.choice(my_ownership_not_rented)
            h_to_sell.props["my_type"] = "mortgage"
            self.put_on_market(h_to_sell)
        # if all the houses are rented, select the one that yields the highest surplus
        else:
            # calculate the surplus profit from selling each house in my_ownership
            surplus = [hh.props["my_ownership"][i].props["sale_price"] - hh.props["mortgage"][i] for i in range(len(household.props["my_ownership"]))]
            # indicate the surplus from selling my_house is zero
            surplus[hh.props["my_ownership"].index(hh.props["my_house"])] = 0
            # select a house to sell
            i_to_sell = surplus.index(max(surplus))
            h_to_sell = hh.props["my_ownership"][i_to_sell]
            # manage the occupier (since the house is rented to someone)
            occupier = h_to_sell.props["my_occupier"]
            self.evict(occupier)
            self.enter_market(occupier, "rent")
            # put the house on the market
            h_to_sell.props["my_type"] = "mortgage"
            self.put_on_market(h_to_sell)
    
    def assign_local_realtors(self, house:House, loc_index:int = -1):
        """
        Find a local realtor

        Parameters
        ----------
        house: House agent
        loc_index: int, default -1
            at -1, the house location index uses is house.location_index
        """
        # find the location index
        if loc_index == -1:
            h_loc_index = int(house.location_index)
        else:
            h_loc_index = int(loc_index)
        dists_from_realtors = {}
        # assign local realtor
        for r_loc_index in self.realtors_indices:
            dist_temp = self.distance(h_loc_index, r_loc_index)
            dists_from_realtors[r_loc_index] = dist_temp
            if dist_temp <= self.inputs["realtor_territory"]:
                house.props["local_realtors"].append(self.space.at[r_loc_index, "realtors"][0])
        if house.props["local_realtors"] == list():
            r_loc_index_alternative = min(dists_from_realtors, key=dists_from_realtors.get)
            house.props["local_realtors"].append(self.space.at[r_loc_index_alternative, "realtors"][0])

    def record_to_realtor_locality(self, house:House):
        """
        Adds the house to the realtor locality

        Parameters
        ----------
        house: House
        """
        for realtor in house.props["local_realtors"]:
            realtor.props["locality_houses"].append(house)

    def record_price(self, house:House, record_sale:bool=False, record_rent:bool=False):
        """
        Records the house rent or price to the realtors based on house type. 
        If both record_sale and record_rent are set to False, record both rent and price.

        Parameters
        ----------
        house: House
        record_sale: bool, default=False
            Record the price of the house to its local realtors if True
        record_rent: bool, default=False
            Record the rent of the house to its local realtors if True
        """
        record = {}
        for realtor in house.props["local_realtors"]:
            record["house"] = house
            record["date"] = self.ticks
            if record_sale == True and record_rent == False:
                record["sale_price"] = house.props["sale_price"]
                record["rent_price"] = 0
                record["transaction"] = "sale"
                #realtor.props["mean_price"] = mean([p for p in realtor.props["sale_price"] if p != 0])
            elif record_sale == False and record_rent == True:
                record["sale_price"] = 0
                record["rent_price"] = house.props["rent_price"]
                record["transaction"] = "rent"
                #realtor.props["mean_rent"] = mean([r for r in realtor.props["rent_price"] if r != 0])
            else:
                record["sale_price"] = house.props["sale_price"]
                record["rent_price"] = house.props["rent_price"]
                record["transaction"] = "unknown"
                #realtor.props["mean_price"] = mean([p for p in realtor.props["sale_price"] if p != 0])
                #realtor.props["mean_rent"] = mean([r for r in realtor.props["rent_price"] if r != 0])
            realtor.props["records"].append(record)
        self.records.append(record)
    
    def remove_record(self, house:House):
        """
        Removes a house from the records of its realtors

        Parameters
        ----------
        house: House object

        Return
        ------
        boolean
            True: the record has been removed
            False: the record was not found
        """
        status = False
        for realtor in house.props["local_realtors"]:
            # find all the records of the house in the realtor's records archive
            house_records = [realtor.props["records"][r] for r in range(len(realtor.props["records"])) if realtor.props["records"][r]["house"] == house]
            # remove all the found records (if any)
            for record in house_records:
                realtor.props["records"].remove(record)
                status = True
        return status

    def evaluate(self, house:House):
        """
        Evaluates a house for all realtors.
        
        Parameters
        ----------
        house: House object
        sale_price: boolean

        Return
        ------
        list{int}
            List of prices or rents
        """
        #normalisation = 1
        #multiplier = house.props["quality"] * ((1 + self.inputs["realtor_optimism"]) / 100) * normalisation

        h_old_price = copy.deepcopy(house.props["sale_price"])
        h_old_rent = copy.deepcopy(house.props["rent_price"])

        evaluation = list()

        if house.props["for_sale?"] == True:
            for realtor in house.props["local_realtors"]:
                ## find the houses within both the locality of the input house and its realtor
                local_sales = [
                    realtor.props["records"][i]["sale_price"] for i in range(len(realtor.props["records"])) \
                    if realtor.props["records"][i]["transaction"] == "sale" \
                    and self.distance(house, realtor.props["records"][i]["house"]) <= self.inputs["locality"]
                ]
                if len(local_sales) > 0:
                    evaluation.append(median(local_sales))
                else:
                    evaluation.append(realtor.props["mean_price"])
            
        elif house.props["for_rent?"] == True:
            for realtor in house.props["local_realtors"]:
                ## find the houses within both the locality of the input house and its realtor
                local_rents = [
                    realtor.props["records"][i]["rent_price"] for i in range(len(realtor.props["records"])) \
                    if realtor.props["records"][i]["transaction"] == "rent" \
                    and self.distance(house, realtor.props["records"][i]["house"]) <= self.inputs["locality"]
                ]
                if len(local_rents) > 0:
                    evaluation.append(median(local_rents))
                else:
                    evaluation.append(realtor.props["mean_rent"])
        return evaluation

    def follow_chain(self, household:Household, first_household:Household):
        """
        Checks the chain of transactions for a given household

        Parameters
        ----------
        household: Household object
            The buyer/tenant wanting to check the chain to make an offer
        first_household: Household object
            The first household making an offer in the current chain

        Return
        ------
        boolean
            True: the chain is complete and the households in the chain should make the transactions
            False: the chain is not complete and the households in the chain should not make the transactions
        """
        # if the household did not make any offer or is not on the market in the first place, False
        if household.props["made_offer_on"] is None or household.props["on_market?"] == False: return False

        # if the buyer is on the mortgage or buy-to-let market
        if household.props["on_market_type"] == "mortgage" or household.props["on_market_type"] == "buy-to-let":
            buyer = household
            seller = buyer.props["made_offer_on"].props["my_owner"]
            # if there is no seller (i.e., house is not owned), report a true chain
            if seller is None: return True
            # if the seller has more than one house (i.e., seller does not need to find another house to buy before the transaction), report a true chain
            if len(seller.props["my_ownership"]) > 1: return True
            # if the buyer is the same as the seller (i.e., they are exchanging their houses), True
            if buyer == seller: return True
            # if seller is the same as the first link in the change (i.e., there is a loop of exhcanges), True
            if seller == first_household: return True
            # else, meaning, if the seller has one house, check if the seller has a confirmed house to buy before making the transaction
            return self.follow_chain(seller, first_household)
        
        # if the buyer is on the rent market
        if household.props["on_market_type"] == "rent":
            tenant = household
            occupier = tenant.props["made_offer_on"].props["my_occupier"]
            # if there is no occupier (i.e., the house is vacant and can be directly rented), True
            if occupier is None: return True
            # if the occupier of the house is the first household in the link
            if occupier == first_household: return True
            # else, meaning, if there is an occupier, check if that occupier found another house to rent or not before making the transaction
            return self.follow_chain(occupier, first_household)

    def manage_ownership_buyer(self, buyer:Household):
        """
        Manage ownership parameters of a buyer

        Parameters
        ----------
        buyer: Household object
        """
        current_house = buyer.props["my_house"]
        new_house = buyer.props["made_offer_on"]
        self.record_price(new_house, record_sale=True)
        # buyers on a mortgage market
        if buyer.props["on_market_type"] == "mortgage":
            # manage the situation when a tenant is buying and moving from their current my_house
            if current_house is not None and current_house.props["my_type"] == "rent":
                current_house.props["my_occupier"] = None
                current_house.props["rented_to"] = None
                current_house.props["offered_to"] = None
                self.put_on_market(current_house)
        
            # manage the parameters of the new house and take it off the market
            new_house.props["my_type"] = "mortgage"
            new_house.props["my_owner"] = buyer
            new_house.props["my_occupier"] = buyer
            new_house.props["rented_to"] = None
            new_house.props["offered_to"] = None
            new_house.props["for_sale?"] = False
            new_house.props["for_rent?"] = False
            # manage the parameters of the buyer
            buyer.props["homeless"] = 0
            buyer.props["my_type"] = "mortgage"
            buyer.props["date_of_acquire"] = self.ticks
            buyer.props["my_house"] = new_house
            buyer.props["my_ownership"] = [new_house]
            buyer.props["made_offer_on"] = None
            buyer.props["on_market?"] = False
            buyer.props["on_market_type"] = None
            # physically move the buyer to the new house
            self.move_agent(buyer, new_house.location_index)
        
        # buyers on a buy-to-let market
        if buyer.props["on_market_type"] == "buy-to-let":
            # manage the parameters of the new house
            new_house.props["my_type"] = "rent"
            new_house.props["my_owner"] = buyer
            new_house.props["my_occupier"] = None
            new_house.props["offered_to"] = None
            new_house.props["rented_to"] = None
            self.put_on_market(new_house)
            new_house.props["rent_price"] = max([
                max(self.evaluate(new_house)), 
                buyer.props["repayment"][-1]
                ])
            # manage the parameters of the buyer
            buyer.props["my_ownership"].append(new_house)
            buyer.props["made_offer_on"] = None
            buyer.props["on_market?"] = False
            buyer.props["on_market_type"] = None

    def manage_ownership_seller(self, seller:Household, seller_house:House):
        """
        Manage ownership parameters of a seller given the house being sold

        Parameters
        ----------
        seller: Hosuehold object
        seller_house: House object
        """
        seller.props["my_ownership"].remove(seller_house)

    def manage_ownership_tenant(self, tenant:Household):
        """
        Manage the ownership parameters of a tenant

        Parameters
        ----------
        tenant: Household object
        """
        new_house = tenant.props["made_offer_on"]
        old_house = tenant.props["my_house"]
        self.record_price(new_house, record_rent=True)
        # manage the parameters of the tenant
        tenant.props["homeless"] = 0
        tenant.props["my_type"] = "rent"
        tenant.props["my_house"] = new_house
        tenant.props["my_rent"] = new_house.props["rent_price"]
        tenant.props["my_ownership"] = list()
        tenant.props["made_offer_on"] = None
        tenant.props["on_market?"] = False
        tenant.props["on_market_type"] = None
        # manage the parameters of the new house
        ## make sure the occupier unregisters the house from their my-house parameter
        ## the occupier will later rent another house (this is checked within the follow-chain function)
        if new_house.props["my_occupier"] is not None: new_house.props["my_occupier"].props["my_house"] = None
        new_house.props["my_occupier"] = tenant
        new_house.props["rented_to"] = tenant
        new_house.props["for_sale?"] = False
        new_house.props["for_rent?"] = False
        if old_house is not None:
            old_house.props["my_occupier"] = None
            old_house.props["rented_to"] = None
            self.put_on_market(old_house)
        # physically move the tenant to the new house
        self.move_agent(tenant, new_house.location_index)

    def manage_surplus_buyer(self, buyer:Household):
        """
        Manage the finances of a buyer

        Parameters
        ----------
        buyer: Household object
        """
        new_house = buyer.props["made_offer_on"]
        price = new_house.props["sale_price"]

        # if sale price of new house is higher than capital (i.e., buyer has to apply for a mortgage)
        if new_house.props["sale_price"] > buyer.props["capital"]:
            mortgage_temp = new_house.props["sale_price"] - buyer.props["capital"]
            buyer.props["capital"] = 0
            repayment_temp = (mortgage_temp * self.interest_per_tick) / (1 - (1 + self.interest_per_tick) ** (- self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"]))
            # manage the mortgage and repayment parameters
            buyer.props["mortgage"].append(mortgage_temp)
            buyer.props["mortgage_initial"].append(mortgage_temp)
            buyer.props["repayment"].append(repayment_temp)
            buyer.props["income_rent"].append(0)
            buyer.props["rate"].append(self.interest_per_tick)
            # manage the rate duration for mortgage and BTL owners separately
            if len(buyer.props["my_ownership"]) == 0:
                buyer.props["rate_duration"].append(random.randint(self.inputs["min_rate_duration_M"], self.inputs["max_rate_duration_M"]))
            else:
                buyer.props["rate_duration"].append(random.randint(self.inputs["min_rate_duration_BTL"], self.inputs["max_rate_duration_BTL"]))
            buyer.props["mortgage_duration"].append(self.inputs["mortgage_duration"] * self.inputs["ticks_per_year"])

        # if sale price of new house is less than capital (i.e, buyer can pay in cash)
        else:
            buyer.props["capital"] -= new_house.props["sale_price"]
            buyer.props["mortgage"].append(0)
            buyer.props["mortgage_initial"].append(0)
            buyer.props["repayment"].append(0)
            buyer.props["income_rent"].append(0)
            buyer.props["rate"].append(0)
            buyer.props["rate_duration"].append(None)
            buyer.props["mortgage_duration"].append(None)

    def manage_surplus_seller(self, seller:Household, seller_house:House):
        """
        Manage finances of a seller given the house being sold

        Parameters
        ----------
        seller: Hosuehold object
        seller_house: House object
        """
        i = seller.props["my_ownership"].index(seller_house)
        mortgage_temp = seller.props["mortgage"][i]
        surplus = seller_house.props["sale_price"] - mortgage_temp
        seller.props["capital"] += surplus
        del seller.props["mortgage"][i]
        del seller.props["mortgage_initial"][i]
        del seller.props["repayment"][i]
        del seller.props["income_rent"][i]
        del seller.props["rate"][i]
        del seller.props["rate_duration"][i]
        del seller.props["mortgage_duration"][i]

    def manage_surplus_tenant(self, tenant:Household):
        """
        Manage the finances of a tenant making an offer

        Parameters:
        -----------
        tenant: Household object
        """
        new_house = tenant.props["made_offer_on"]
        tenant.props["my_rent"] = new_house.props["rent_price"]

    def manage_surplus_landlord(self, landlord:Household, landlord_house:House):
        """
        Manage finance of landlord given the house to rent

        Parameters
        ----------
        landlord: Household object
        landlord_house: House object
        """
        i = landlord.props["my_ownership"].index(landlord_house)
        landlord.props["income_rent"][i] = landlord_house.props["rent_price"]
            



            

            







            
