



## **The Intelligent Enterprise** 

Design and build a delivery planning system for Waypoint Group, then develop the predictions that help its team plan ahead. This brief sets out the business problem, phase requirements, datasets, judging criteria, and submission deadlines. 

### **How the competition works** 

Tech-Triathlon 2026 follows one business challenge across three phases over 15 days. We release this brief and all datasets on Day 1. There are no separate challenge releases. All dates and times in this brief use Sri Lanka time (Asia/Colombo, UTC+05:30). 

|**Milestone**|**Day**|**Date and time in Sri Lanka**|
|---|---|---|
|**Brief and all datasets released**|1|Friday, September 25, 2026, at 12:01 AM|
|**Designathon deadline**|5|**Tuesday, September 29, 2026, at 11:59 PM**|
|**Hackathon deadline**|10|**Sunday, October 4, 2026, at 11:59 PM**|
|**Datathon deadline**|15|**Friday, October 9, 2026, at 11:59 PM**|



Your Hackathon build must follow your Designathon submission. Judges will assess the continuity between the two. If you miss a phase, you may continue to the next, but you will receive zero for the missed phase. All three phases contribute equally to your overall score. 

### **Waypoint Group** 

Waypoint Group (Pvt) Ltd is a fictional Sri Lankan retail group with three brands sharing one distribution network. 

|**Brand**|**Outlets**|**Goods**|**Delivery schedule**|
|---|---|---|---|
|**Waypoint Fresh**|80|Groceries, chilled and frozen goods; a|Daily; before stores open at|
|||wide range of products|8 AM|
|**Waypoint Style**|25|Hanging garments and cartons|Weekly, with seasonal peaks|
|**Waypoint Tech**|15|Appliances and|As needed; high-value,|
|||consumer electronics|fragile goods|



The network serves 120 outlets through a distribution center in Peliyagoda and a regional hub in Kandy. Its 60 vehicles include 12 refrigerated trucks, 40 dry-box trucks, and eight small vans for outlets that larger vehicles cannot reach. Four of the vans are refrigerated, giving the fleet 16 vehicles that can carry chilled goods. Each vehicle operates from its assigned depot. 

Challenge Booklet · Tech-Triathlon 2026 

**03** 





### **The business problem** 

Waypoint’s three brands compete for the same delivery capacity. Fresh needs deliveries to reach its 80 supermarkets before they open at 8 AM. Chilled orders require refrigerated vehicles, and some outlets can only be reached by van. Style’s garments fill a vehicle’s available volume before reaching its weight limit, and around half of its stores are in malls with fixed delivery windows. Tech’s appliances are heavy, fragile, and valuable, with demand that varies from day to day. 

On most days, the fleet cannot meet every brand’s needs at once. Dispatchers must allocate capacity while accounting for outlet access, delivery windows, and weekly fuel quotas. When demand exceeds capacity, they must decide which orders to defer and explain the consequences. 

#### **How orders reach the dispatcher** 

Store managers place orders according to their brand’s delivery schedule. Fresh outlets order dry groceries for every operating day they trade and place separate chilled orders on several days each week. A Fresh outlet can therefore have two orders for the same delivery day. Style orders weekly for a scheduled delivery day, with larger orders ahead of seasonal peaks. Tech orders as needed, often for a single large item. 

Orders for the next day close at 4 PM. After the cutoff, the dispatcher plans against the confirmed orders, available vehicles, and operating constraints. Orders received after the cutoff wait for the following run. 

#### **How Waypoint works today** 

Dispatchers plan deliveries using spreadsheets and their network knowledge. They communicate instructions through phone calls, conversations at the loading dock, and printed run sheets. Once vehicles leave, dispatchers have no shared view of progress. Drivers report problems by phone, and changes reach each person through separate calls. Handwritten notes provide only a limited record of deliveries and deferral decisions. 

#### **Problems your solution must address** 

- **Planning is fragmented.** Orders arrive by phone or message and are entered again in a spreadsheet. The plan depends on one dispatcher’s knowledge. 

- **Delivery progress is difficult to track.** Dispatchers usually learn about a problem only after a driver has reached the outlet. 

- **Deferrals lack a clear record.** Decisions made under pressure can leave the same outlet unserved on consecutive runs. 

- **Communication does not support feedback.** Printed run sheets and verbal instructions provide no reliable way to record proof of delivery or flag a loading shortfall before departure. 

- **Demand is difficult to anticipate.** Waypoint cannot estimate the vehicles, drivers, or refrigerated capacity it will need ahead of paydays and festivals. 

- **Service time and lateness are not predicted.** Dispatchers discover delays after they have affected a delivery. 

- **Field connectivity is unreliable.** The solution must support work without a connection and reconcile records when connectivity returns. 

Challenge Booklet · Tech-Triathlon 2026 

**04** 





### **Operating constraints** 

#### **Vehicles** 

Every vehicle has a weight limit and a volume limit. A load must satisfy both. 

- Only refrigerated vehicles may carry chilled or frozen goods. Refrigerated vehicles may also carry ambient goods. Ambient vehicles cannot carry chilled or frozen goods. 

- Each vehicle has a weekly fuel quota. Route distance consumes that allowance. 

- A vehicle can run up to two routes per day. Waypoint operates Monday through Saturday. 

- Each vehicle has a driver. Driver availability is not a separate constraint when allocating the existing fleet. 

#### **Outlets** 

Every outlet has a delivery window. Fresh deliveries must arrive before stores open at 8 AM, although individual outlets’ windows may differ. 

Mall outlets accept deliveries only within the mall’s fixed access window. 

- Outlets marked `van_only` cannot be served by trucks. 

- Unloading conditions vary by outlet. Goods may arrive through a rear dock, at the curb, or through a shared mall loading bay. 

#### **Demand and operating days** 

Paydays, festivals, weekends, and monsoon conditions affect demand or travel time. Use `calendar.csv` to identify operating dates. 

When demand exceeds capacity, the dispatcher must decide which orders move to the next run and record the reason. 

#### **Connectivity** 

Mobile coverage can drop across hill country, the Kandy corridor, and rural districts. 

Work away from the depot must remain usable offline. Records must reconcile when the connection returns. 

Challenge Booklet · Tech-Triathlon 2026 

**05** 





### **The four user roles** 

Design the system around the conditions each person works in and the information they need from other roles. 

##### **Dispatcher** 

##### **Loader** 

Works at a large screen in the Peliyagoda planning office with stable connectivity. Builds the daily plan using a spreadsheet and knowledge of outlet restrictions and vehicle capabilities. 

Needs visibility into delivery progress and problems after vehicles leave the depot. 

Needs to explain deferral decisions and identify outlets that have already been skipped. 

Works at the Peliyagoda or Kandy warehouse dock using a shared tablet or terminal. Printed loading lists can become outdated when plans change. 

Needs the stop sequence so goods can be loaded in an order that supports unloading. 

Needs to flag missing or damaged items before a vehicle leaves. 

##### **Driver** 

##### **Store manager** 

Works on the road using a personal phone. Currently relies on a paper run sheet and phone calls for changes. Design interactions for use when safely stopped. 

Works at the outlet counter using a desktop or phone. Places orders by phone or message without confirmation that they received or scheduled them. 

Needs to record delivery outcomes and proof of delivery so disputes do not depend on memory. Needs to record work offline when coverage drops and synchronize it when connectivity returns. 

Needs an expected arrival time to schedule staff to receive goods. 

Needs clear notice when an order is deferred, plus a way to confirm receipt and report issues. 

Challenge Booklet · Tech-Triathlon 2026 

**06** 





### **Your objective** 

Build a system that connects ordering, planning, loading, delivery, and receipt across these four roles. Help Waypoint make delivery decisions it can explain and plan capacity ahead of demand. The Designathon defines the experience, and the Hackathon implements it. The Datathon develops estimates of outlet service time, arrival lateness, and future demand volume to support planning. 

The workflow below shows what each role needs to do. Service-time and lateness predictions support delivery planning. Demand forecasts support fleet planning for future weeks. 

|**Stage**|**Role**|**System requirement**|
|---|---|---|
|**Place order**|Store manager|Capture and confirm the order before the cutoff.|
|**Close orders**|Dispatcher|Bring confirmed orders into one queue.|
|**Plan and allocate**|Dispatcher|Assign served orders to vehicles and trips; identify<br>deferred orders.|
|**Load**|Loader|Load for the planned stop sequence and flag shortfalls.|
|**Deliver**|Driver|Follow the route and record each stop, including<br>while offline.|
|**Confirm receipt**|Store manager|Confirm what arrived and report issues.|
|**Plan future capacity**|Dispatcher|Use demand forecasts to plan vehicles, drivers, and<br>refrigerated capacity.|



### **Shared datasets** 

All three phases use the same 120 outlets, 60 vehicles, two depots, and calendar. Use these records consistently across your designs, working system, and models. All competition data is synthetic and does not represent a real company, outlet, or person. 

|**File**|**Purpose**|
|---|---|
|**`outlets.csv`**|The 120 outlets, including brand, district, depot, access restrictions, and<br>delivery windows.|
|**`vehicles.csv`**|The 60 vehicles, including type, temperature capability, weight and volume limits,<br>fuel profile, and home depot.|
|**`calendar.csv`**|Dates across the history and forecast horizon, with payday, festival, monsoon, and<br>operating-day information.|



Additional Datathon files and their key columns are documented later in this brief. 

##### **Click Here to Access the Datasets** 

Challenge Booklet · Tech-Triathlon 2026 

**07** 





# **DESIGNATHON CHALLENGE** 





### **Designathon** 

###### **Submission due Day 5** 

Design one system that helps all four roles complete the delivery workflow. Show how you understand the operation, which problems you prioritize, and why your scope is appropriate. 

Connect the role-specific experiences. A dispatcher’s decision should reach the loader, and a driver’s delivery record should give the store manager information they can act on. 

#### **Scope** 

Design the screens each role needs to complete its work, including at least one fully developed screen for a failure scenario. Explain your choices. Judges will assess prioritization and restraint, as well as the quality of the experience. 

#### **Failure scenarios** 

Design at least one screen for a situation in which the normal workflow breaks down. This is called a degradation screen in the judging criteria. Choose the scenario, name it, and explain in a short paragraph why it matters to Waypoint. You may include more than one, but response quality matters more than the number of scenarios. 

#### **Deliverables** 

- **User personas.** Include one persona for each role, grounded in the working conditions and needs in this brief. 

- **Screen flows.** Show each role’s screens and include a one-paragraph rationale for every screen, explaining its purpose and priorities. 

- **Degradation screens.** Include at least one fully designed failure scenario, with its name and rationale. 

- **High-fidelity prototype.** Use a design tool of your choice to demonstrate the flows you designed. 

- **Demo Video.** Upload a three to five minute demo video on YouTube as an unlisted video. The video should provide a walkthrough of your design workflow and discuss any assumptions that influenced your design for the given scenario. Submit the YouTube URL to the submission form. 

- **AI tool disclosure.** Explain which work was AI-assisted, which was not, and how you used the tools. 

- **Core tradeoff explanation, optional.** Use up to one page or one diagram to explain your main design tradeoff. 

- **Style guide, optional.** 

Challenge Booklet · Tech-Triathlon 2026 

**09** 





#### **Judging criteria** 

|**Criterion**|**Weight**|
|---|---|
|**Problem framing**|**25%**|
|**Understanding of user context**|**20%**|
|**Degradation screen quality**|**15%**|
|**Domain accuracy**|**10%**|
|**Scope and prioritization**|**15%**|
|**Visual and interaction design, including consistency across roles**|**15%**|



#### **Submission** 

Organize your personas, screen flows, rationale, degradation screens, diagrams, AI tool disclosure, core tradeoff explanation (optional), and style guide (optional) into one design file with distinct pages. Export the file using `TeamName_Designathon` as the base filename. Compress it as `TeamName_Designathon.zip` and upload it through the submission form. Upload shareable links to your prototype and demo video onto the submission form as well. 

Submit by **Tuesday, September 29, 2026, at 11:59 PM** Sri Lanka time (Day 5). Judges will assess the design submitted at that deadline. You may refine the solution during the Hackathon, but document significant departures from the submitted design in your README. 

Deadline for submissions: **Tuesday, September 29, 2026, at 11:59 PM** ↗ **Submission Form:** <u>https://forms.gle/H6dqUZP6pXdGC8Go8</u> 

Challenge Booklet · Tech-Triathlon 2026 

**10** 





# **HACKATHON CHALLENGE** 





### **Hackathon** 

###### **Submission due Day 10** 

Build the flows, screens, and capabilities in your Designathon submission. That design is your implementation specification, and judges will assess how faithfully you deliver it. 

Every submission must meet the following requirements. 

Provide a responsive web application that lets a judge complete the delivery workflow across all four roles, from planning through loading and delivery to receipt at the outlet. Judges will assess the driver and loader experiences on phone-sized screens. Native applications are optional additions to the required web application. 

Make the system respect the operating constraints. Plans must account for capacity, temperature requirements, outlet access, delivery windows, and fuel quotas. 

#### **Planning and allocation** 

Your system must assign orders to vehicles and trips and handle a day when demand exceeds available capacity. You may use automatic allocation, assisted planning, or manual decisions with validation. Whatever approach you choose, the system must produce an allocation that respects the operating constraints and identifies deferred orders. 

#### **Judge walkthrough** 

Add a numbered walkthrough to your README that a judge can follow across all four roles, from planning to completed delivery. Seed the system with the shared datasets and at least one realistic delivery day so the walkthrough works on a fresh installation. 

#### **Deliverables** 

**Deployed system.** Provide a public URL and credentials for four seeded accounts, one per user role. 

**Source repository.** Use a GitHub monorepo named `TeamName_SolutionName` . It must contain: 

- A README with setup and configuration instructions, seeded account details, the judge walkthrough, and significant departures from the Designathon submission. 

- A Docker Compose file and an `.env.example` file at the repository root. The command `docker compose up` must start the complete stack, including the database and seed data. 

- A `docs` folder at the repository root containing an architecture diagram and data model, showing the main components and how the system stores and connects its data. 

- An AI tool disclosure in the same docs folder, explaining which work was AI-assisted, which was not, and how you used the tools. 

**Demo video.** Submit an unlisted YouTube video lasting five to eight minutes. Show all four roles completing the walkthrough, followed by a brief explanation of the code and architecture. 

Challenge Booklet · Tech-Triathlon 2026 

**12** 





#### **Judging criteria** 

|**Criterion**|**Weight**|
|---|---|
|**Functional completeness across all four roles**|**20%**|
|**Planning and allocation engine**|**20%**|
|**Degradation, offline operation, and recovery**|**10%**|
|**Fidelity to the Day 5 design**|**10%**|
|**Engineering quality and architecture**|**25%**|
|**Creativity**|**5%**|
|**Demo video**|**10%**|



#### **Submission** 

Submit the repository link, deployed URL, seeded account credentials, and demo video link through the submission form. 

Submit by **Sunday, October 4, 2026, at 11:59 PM** Sri Lanka time (Day 10). Code pushed after the deadline will not be considered. Keep the deployment live throughout the review period and, if your team advances, through the semifinal and Grand Finale periods. 

Deadline for submissions: **Sunday, October 4, 2026, at 11:59 PM** 

↗ **Submission Form:** <u>https://forms.gle/WurHAKjbq2XEZQhbA</u> 

Challenge Booklet · Tech-Triathlon 2026 

**13** 

