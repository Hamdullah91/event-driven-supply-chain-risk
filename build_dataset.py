import json
import random
from collections import Counter

# ---------------------------------------------------------------------------
# SUPPLY_DISRUPTION (50)
# ---------------------------------------------------------------------------
supply_disruption = [
    "A shortage of packaging substrates has forced a Malaysian chip assembler to scale back weekend shifts.",
    "Battery pack lines in three countries slowed this week after cathode shipments from a South American supplier failed to arrive on schedule.",
    "An aircraft-seat maker says it has been unable to secure enough specialized foam for its cushions since late last month, pushing back deliveries to two airlines.",
    "Persistent shortages of specialty gases have slowed wafer output at several Taiwanese foundries.",
    "A battery-pack assembler has burned through its buffer stock of separator film and has yet to line up a new supplier.",
    "A supplier's failure to deliver landing-gear components on time has delayed aircraft assembly at a US plant.",
    "Orders for a niche photoresist chemical have gone unfilled for six weeks, and buyers in South Korea say they have no backup source.",
    "Two European battery plants have trimmed output because the nickel sulfate they rely on has not been delivered in full for over a month.",
    "A French aerostructures firm reports it cannot source enough titanium fasteners to keep pace with its delivery schedule.",
    "Chip packaging lines in Vietnam sit idle as promised wire-bonding equipment parts remain stuck en route.",
    "Graphite anode material shortages have pushed back cell production at a mid-sized battery maker.",
    "After a regional trucking strike stretched into its second week, several fabs report they have run low on bulk chemicals needed for etching.",
    "Connector backlog grounds assembly at avionics supplier.",
    "A Chinese wafer producer says a lack of available neon gas is constraining its output.",
    "A landslide blocked the only access road to a remote lithium site in the Andes for eleven days, and cell makers downstream say they are rationing stock while shipments catch up.",
    "A supplier missed three consecutive shipment windows, leaving a chipmaker short of the specialty resin used in packaging.",
    "A Japanese sensor-parts maker has gone quiet on delivery dates after saying its own inputs are running low, leaving two aircraft manufacturers waiting.",
    "Cell assembly stalls in Poland as promised electrolyte batch fails to show.",
    "Chipmakers are reporting extended lead times for microcontrollers due to component shortages.",
    "Deliveries of a specialized adhesive used in composite wing panels have been pushed back indefinitely, and the affected manufacturer has not named a replacement source.",
    "Smartphone assembly at one plant has slowed to half capacity; the company blames unfilled orders for a display driver chip that has not arrived since July.",
    "A cobalt shortage has left a battery-cell producer unable to meet its second-quarter targets.",
    "Titanium backlog leaves jet-engine parts maker scrambling.",
    "A processing plant in Africa that refines a rare gas used in chipmaking has fallen behind on outbound shipments for two months, and several fabs abroad say their reserves are nearly gone.",
    "Persistent supply-chain disruption has left several fabless design firms unable to secure enough advanced packaging capacity.",
    "In a note to investors, the company said it has been unable to source enough battery-grade manganese sulfate to run its cathode line at full rate.",
    "A regional carrier says spare parts for one of its aircraft types have not arrived in over two months, grounding three planes.",
    "A shortage of ultra-pure water treatment chemicals is constraining chip production in Taiwan.",
    "The automaker's battery line ran two shifts short this week; it cited a supplier that has not delivered separator film since early last month.",
    "Delivery delays for avionics wiring harnesses have disrupted final assembly at an aircraft manufacturer.",
    "Photomask orders pile up as vendor falls silent on delivery.",
    "Shipments of battery-grade lithium hydroxide bound for a European gigafactory have been stuck at a transfer hub for nearly a month.",
    "A components shortage has forced a contract manufacturer to halt several assembly lines.",
    "A supplier of cockpit displays has fallen more than ten weeks behind on orders, and two customers say they are now looking elsewhere.",
    "Assembly plants in Southeast Asia say they are running through their last reserves of a specialty solder after a supplier's shipments stopped arriving without explanation.",
    "Nickel supply shortages are limiting how many battery packs a cell maker can produce this quarter.",
    "Composite-panel maker waits on resin shipment that never came.",
    "A dockworkers' slowdown at a major transshipment port has left crates of packaging substrates sitting unclaimed, and two chipmakers say their lines will run dry within days.",
    "A graphite supplier's missed deliveries have left a battery maker without enough anode material to meet orders.",
    "Analysts note that lead times for a critical flight-control sensor have stretched past five months, with the manufacturer citing an unnamed supplier's ongoing shortfall.",
    "Chip production has slowed after a key raw-wafer supplier failed to meet delivery commitments.",
    "A cobalt exporter in central Africa has been unable to move material out of the region for weeks, and refiners overseas say their stockpiles are thinning fast.",
    "Fastener drought slows jet-engine final assembly.",
    "A prolonged shortage of gallium arsenide wafers is affecting several specialty chip producers.",
    "Orders for a specialized battery-can component have gone unfulfilled since the spring, and the buyer has been forced to draw down inventory it had planned to keep in reserve.",
    "Aircraft-parts backlogs have worsened after a connector supplier could not keep pace with demand.",
    "The order was placed four months ago; it still has not shipped, and the buyer's line has been running on borrowed inventory ever since.",
    "Cathode buyers turn to spot market as contracted tonnes fail to arrive.",
    "A shortage of bonding wire has disrupted chip packaging operations at several plants.",
    "An industry group's latest survey found that more than half of aerostructure suppliers have had at least one order go unfilled by their upstream material provider this year.",
]

# ---------------------------------------------------------------------------
# REGULATION_CHANGE (50)
# ---------------------------------------------------------------------------
regulation_change = [
    "Chipmakers operating in the state will need to cut wastewater discharge levels by half under a new environmental rule effective next year.",
    "Battery recyclers across the bloc will soon be required to prove at least 95 percent of lithium is recovered from every cell they process.",
    "Aviation authorities have updated inspection requirements for composite fuselage sections.",
    "Fab operators face tighter chemical-handling audits from next spring.",
    "Cell makers will need to redesign their quality-control paperwork after inspectors began requiring full traceability for every battery cell produced.",
    "New safety certification standards for avionics software have been finalized by the civil aviation authority.",
    "Foundries in the country must now log every water sample taken from onsite treatment ponds; the requirement takes effect at the start of the next fiscal year.",
    "Manufacturing rules for battery-pack fire safety have been tightened following a series of independent reviews.",
    "In an internal memo, the supplier said it will need to retrain its entire quality team to meet updated recordkeeping requirements set by the aviation regulator.",
    "Cleanroom certification overhaul to hit local chip plants.",
    "Aircraft-parts makers must retain full traceability records for a decade under updated recordkeeping requirements.",
    "Any plant recycling lithium-ion packs will need an updated environmental permit before restarting idle lines, under rules taking effect this quarter.",
    "Updated safety standards for cleanroom chemical storage have been issued for chip fabrication plants.",
    "Composite-material suppliers will be subject to quarterly on-site audits rather than the current annual review, starting in the new year.",
    "Analysts expect compliance costs to rise after inspectors gained authority to test emissions at any fab without advance notice.",
    "A new industrial standard requires battery makers to disclose the full material composition of every cell sold domestically.",
    "Sensor-parts makers brace for stricter calibration audits.",
    "Because two nearby residential areas raised air-quality complaints, fabs in the district must now install additional filtration before year's end.",
    "Manufacturing standards for flight-control wiring have been revised by the aviation authority.",
    "Cell producers setting up in the country will need to pass a new fire-suppression inspection before their first shipment can leave the plant.",
    "Recycling requirements for semiconductor-grade silicon scrap have been formalized under updated industrial rules.",
    "The agency finished a two-year review of maintenance recordkeeping; shops overhauling flight-control components must now retain digital logs for fifteen years instead of seven.",
    "Chip plants told to overhaul chemical storage within a year.",
    "Environmental requirements for cobalt refining wastewater have been tightened by the ministry.",
    "Shops that overhaul navigation units will need certification from a newly created inspection body before they can accept further work.",
    "Several fabs have begun installing new scrubber systems after inspectors raised the minimum standard for volatile-compound capture.",
    "Updated inspection protocols for jet-engine turbine blades have taken effect.",
    "Battery-pack assembly lines will be required to undergo an independent fire-risk assessment before their domestic production license can be renewed.",
    "Safety standards for handling specialty gases in wafer fabs have been strengthened.",
    "Titanium forgers face new heat-treatment documentation rules.",
    "The industrial ministry says every fab must file a quarterly water-use report starting in the coming year, part of a broader push to modernize plant oversight.",
    "Recycling mandates now require battery makers to recover a minimum share of nickel and cobalt from spent packs.",
    "Component testers will need to recalibrate their equipment against a new reference standard before certifying any further flight-control parts.",
    "Inspectors visited twelve fabs last quarter without prior notice; under revised rules, such unannounced visits will now happen at every site at least twice a year.",
    "Compliance requirements for aircraft wiring insulation have been updated by the civil aviation authority.",
    "Cathode plants ordered to log every batch for a decade.",
    "Any facility etching wafers below a certain size will now need a dedicated safety officer on-site during every shift, per updated plant rules.",
    "New industrial standards govern the testing of flight-control actuators.",
    "Cell assembly plants will be required to pass an annual structural inspection under revised manufacturing rules taking effect next year.",
    "Industry consultants say the update effectively doubles the paperwork fabs must keep on hazardous-chemical disposal.",
    "Manufacturing standards for lithography chemical handling have been revised nationwide.",
    "Avionics testers must now log every calibration to the minute.",
    "After several thermal-runaway incidents were reported industry-wide, cell makers must now install additional temperature sensors in every module before sale.",
    "Recycling requirements for used photoresist chemicals have been tightened by regulators.",
    "Maintenance shops overhauling landing gear will need a second sign-off from an independent inspector before returning parts to service.",
    "Inspection requirements for battery-pack thermal management systems have been strengthened.",
    "Wafer plants face new rules on chemical spill reporting.",
    "A newly formed oversight panel will review every avionics supplier's quality system; suppliers that fail the review will lose their certification within ninety days.",
    "Environmental standards for fab cooling-water discharge have been made stricter.",
    "Facilities producing battery separators will need to secure a renewed safety license every two years instead of every five, under an updated compliance schedule.",
]

# ---------------------------------------------------------------------------
# FACILITY_OUTAGE (50)
# ---------------------------------------------------------------------------
facility_outage = [
    "A fire broke out at a semiconductor fab in Japan, halting production for several days.",
    "Battery plant goes dark after overnight incident.",
    "Workers were evacuated from an aerostructures plant after a section of roofing collapsed onto the main assembly floor.",
    "An earthquake forced a Taiwanese chip plant to suspend operations while engineers inspected equipment.",
    "Output at a cathode-material plant has been suspended since equipment on its main line seized up early Tuesday.",
    "A power failure shut down operations at an aircraft-parts factory for most of the day.",
    "Smoke was reported inside a fabrication building shortly before midnight, and the site has not resumed normal operations since.",
    "Flooding forced a battery-cell plant to halt production and begin an emergency cleanup.",
    "Aerostructures site closed indefinitely after structural inspection.",
    "Production at a wafer fab has been suspended following what the company described only as an unplanned electrical event overnight.",
    "An explosion at a materials-processing facility used by an aerospace supplier has halted operations there.",
    "A gigafactory has gone quiet for the third day running after what local officials called an internal safety incident.",
    "Equipment malfunction has forced a chip plant to suspend a portion of its production lines.",
    "Titanium forge dark after weekend equipment failure.",
    "A processing plant that refines rare gases used in chipmaking has been offline since a containment breach was reported over the weekend.",
    "A mine supplying battery-grade lithium has suspended operations after flooding damaged equipment on-site.",
    "Chemical leak halts operations at wafer plant.",
    "A transformer at the plant failed just after 3 a.m., and repair crews say the assembly hall will remain without power, and thus without output, until at least Friday.",
    "A fire at a battery recycling facility has forced an indefinite suspension of operations.",
    "The fab's cleanroom was taken offline after a cooling system failure damaged sensitive equipment overnight.",
    "Structural damage from a storm has closed an aircraft-component warehouse until repairs are complete.",
    "Cell line stopped cold after fire-suppression system triggers unexpectedly.",
    "The company told investors that one of its packaging sites has been idle since a fire alarm triggered an evacuation that has yet to be lifted.",
    "An emergency shutdown was ordered at an avionics plant after a chemical spill was detected.",
    "A materials-processing site that supplies cathode precursor has not reopened since inspectors found cracks in a structural support beam.",
    "Alarms sounded at the facility just before dawn, and by the time the fire was contained, the entire production floor had been evacuated and operations remain suspended.",
    "A warehouse storing battery components was damaged by fire, halting shipments from the site.",
    "Avionics plant goes idle after roof failure.",
    "Wafer output has been zero at the site since a power substation serving the plant failed during a storm.",
    "A structural collapse at a components warehouse has suspended all outbound shipments from the site.",
    "A battery-recycling plant has not processed a single pack since a fire broke out in its shredding area two weeks ago.",
    "Coolant leak forces emergency shutdown at chip plant.",
    "Flooding has forced the temporary closure of a components-assembly plant.",
    "An electrical fault damaged several furnaces beyond immediate repair, and the plant has produced nothing this week, management says.",
    "A gas leak triggered an emergency shutdown at a semiconductor plant.",
    "Inspectors found hairline cracks in a load-bearing wall of the plant, and the site has been closed to production while a full structural review is carried out.",
    "Fab evacuated after overnight fire alarm, restart date unclear.",
    "A fire has shut down a lithium processing plant, and the company has not given a timeline for reopening.",
    "The plant's main assembly hall has been closed since water from a burst pipe damaged wiring throughout the building.",
    "All output at the facility was suspended after a chemical containment failure was discovered during a routine inspection.",
    "An earthquake has damaged an aerospace-components factory, halting production there.",
    "Gigafactory line paused indefinitely after equipment fire.",
    "A backup generator caught fire during a routine test, cutting power to the entire cleanroom, and the plant has been dark since.",
    "A power outage has forced a battery-cell plant to suspend production for the second time this month.",
    "Maintenance crews were testing a new ventilation system when it failed catastrophically, and the plant has not resumed operations since.",
    "A fire has damaged a chip-packaging facility, halting output indefinitely.",
    "Cathode plant shutters after weekend structural failure.",
    "Production has been suspended at the plant since a section of the cleanroom ceiling gave way over the weekend.",
    "An explosion at a chemical storage unit has forced the closure of a wafer-processing plant.",
    "A malfunctioning press damaged critical tooling beyond quick repair, and the plant has not shipped a single cell since.",
]

# ---------------------------------------------------------------------------
# TECHNOLOGY_EMBARGO (50)
# ---------------------------------------------------------------------------
technology_embargo = [
    "Sales of advanced lithography systems to certain overseas chipmakers are now prohibited under updated government rules.",
    "The formulas behind the company's newest battery chemistry are now off-limits to any manufacturer lacking a security clearance.",
    "Flight-control chip blueprints locked away from foreign buyers.",
    "The administration has widened its ban on shipping advanced AI processors to a broader list of destinations.",
    "A licensing deal for next-generation solid-state cell technology fell through this week after the supplier cited new restrictions on sharing its process know-how with overseas partners.",
    "Specialized avionics technology transfer has been blocked for a state-owned aircraft maker.",
    "Access to the design files needed to tape out chips below a certain size has been cut off for engineers without domestic citizenship.",
    "Cathode recipe access shut off to overseas licensees.",
    "A toolmaker has been ordered to stop shipping its most advanced chipmaking machines to certain customers abroad.",
    "Engineers at the joint venture can no longer access the source code behind the aircraft's flight-management software.",
    "A foundry's plans to install next-generation etching tools have collapsed after the toolmaker was barred from shipping the equipment to the site.",
    "Restrictions now bar the transfer of proprietary battery-management software to manufacturers in the region.",
    "Navigation-chip know-how walled off from foreign partners.",
    "A chip-design software vendor has quietly stopped renewing licenses for customers based in the sanctioned jurisdiction.",
    "Advanced semiconductor manufacturing equipment has been added to the list of items requiring special export authorization.",
    "The process used to manufacture silicon-anode material has been classified as sensitive, and licensing it to overseas partners now requires special approval.",
    "The two firms had planned to co-develop a new radar module, but that plan is now on hold after regulators restricted the sharing of the underlying signal-processing technology.",
    "Chip-design software access has been restricted for engineers working in certain countries.",
    "Battery-grade materials recipe kept from foreign cell makers.",
    "A supplier of composite manufacturing tooling has been told it can no longer share its layup process specifications with customers outside a short list of allied countries.",
    "A battery-testing laboratory has been told it can no longer share its degradation-analysis methodology with clients based overseas.",
    "Know-how for producing a next-generation electrolyte additive has been designated too sensitive to license abroad.",
    "Sensor calibration technique off-limits to overseas maintenance shops.",
    "The government has banned the export of advanced AI training chips to a list of restricted destinations.",
    "A planned technology-sharing agreement for advanced cathode coating collapsed after officials classified the process as export-restricted.",
    "The startup had hoped to license its chip-cooling technique overseas, but officials have since deemed the technique sensitive enough to require a special license for any foreign transfer.",
    "Access to classified flight-control system schematics has been cut off for a foreign contractor.",
    "Wafer-thinning process specs deemed too sensitive to export.",
    "A materials science lab has been barred from publishing details of its new anode coating process in any venue accessible to foreign researchers.",
    "Advanced chip-packaging equipment now requires a special license before it can be shipped overseas.",
    "The technical drawings needed to manufacture a new generation of jet-engine turbine blades have been restricted from release to non-domestic suppliers.",
    "Photomask design tools pulled from foreign customer list.",
    "Technology-transfer restrictions now cover next-generation solid-state battery production methods.",
    "A simulation tool used to certify new avionics designs has been reclassified, meaning foreign engineering teams can no longer run it.",
    "A leading chipmaker has been barred from installing its most advanced memory-fabrication tools at an overseas plant.",
    "Engineers had hoped to bring the fast-charging technology to a plant abroad, but new rules classify the underlying charge-control algorithm as too sensitive to transfer.",
    "Composite-curing recipe locked down for exports.",
    "Restrictions on sharing chip-design intellectual property with foreign entities have been expanded.",
    "Detailed process parameters for a new electrode-binder formulation have been withheld from a planned overseas joint venture following a government review.",
    "A cloud-based chip simulation platform has stopped granting new accounts to users connecting from a list of restricted countries.",
    "Specialized radar technology can no longer be licensed to manufacturers outside a short list of approved nations.",
    "Advanced packaging know-how kept in-house under new rules.",
    "The transfer of proprietary battery-recycling technology to foreign partners has been blocked.",
    "A planned technology exchange for next-generation avionics sensors was called off after officials placed the underlying chip design on a restricted list.",
    "A ban on exporting chip-design automation tools to a specific country has been expanded.",
    "De-icing control unit specs locked from overseas manufacturers.",
    "The maintenance manual for the navigation system included proprietary calibration steps that foreign repair shops have now lost access to entirely.",
    "The list of chipmaking equipment requiring export authorization has been expanded to include newer etching tools.",
    "A key patent covering high-density cell architecture has been placed under a technology-control order, barring its licensing abroad.",
    "A flight-simulation software company has stopped issuing licenses that would let foreign engineering teams model its newest cockpit-display system.",
]

# ---------------------------------------------------------------------------
# TRADE_POLICY_CHANGE (50)
# ---------------------------------------------------------------------------
trade_policy_change = [
    "A new tariff of 25 percent will apply to imported semiconductor components starting next quarter.",
    "Shipments crossing into the bloc will now carry an added charge equal to a tenth of their declared value.",
    "Cross-border paperwork burden grows for aircraft-parts shippers.",
    "Import duties on raw silicon wafers have been raised by the finance ministry.",
    "Companies wishing to sell battery cells into the country must now register with customs officials before each shipment clears the border.",
    "A bilateral trade agreement will eliminate duties on aircraft components traded between the two countries.",
    "The two governments finalized a new customs arrangement this week; chip components will now clear the border under a simplified inspection process, though goods from a third country face new scrutiny.",
    "Sanctions have been imposed on a nickel exporter, barring its shipments from entering the bloc.",
    "Goods originating from the flagged region can no longer clear customs at the port, effective immediately.",
    "Border charge on imported chip substrates takes effect.",
    "New export licensing requirements now apply to shipments of aircraft-grade titanium.",
    "Shippers say clearing the border now takes twice as long after customs began requiring an additional certificate of origin for every battery shipment.",
    "Customs rules for chip-manufacturing chemicals crossing the border have been tightened.",
    "Any component crossing into the country will now be subject to a new inspection fee levied at the point of entry.",
    "New paperwork rule slows lithium shipments at the border.",
    "A free-trade agreement covering semiconductor components has been signed by the two countries.",
    "The two nations agreed to let each other's aerospace components cross the border duty-free starting next quarter.",
    "Officials announced a review of import channels for specialty chemicals, and companies bringing the chemicals across the border will now need prior written approval.",
    "Import restrictions on refined cobalt from the sanctioned country have taken effect.",
    "Aerospace fastener imports face new customs scrutiny.",
    "A retaliatory tariff on imported chipmaking equipment has been announced.",
    "Buyers abroad must now file for a permit before any shipment of processed nickel can leave the port.",
    "A new certificate will be required at customs for any aerospace-grade alloy crossing the border, adding several days to typical clearance times.",
    "The list of countries facing export controls on raw gallium has been expanded by trade officials.",
    "Nickel exporters face longer customs queues under new rule.",
    "A trade agreement easing tariffs on aircraft parts has been ratified by both legislatures.",
    "After talks stalled for weeks, one side announced it would impose a new border tax on incoming chip components starting next month.",
    "Sanctions targeting a graphite producer now prevent its exports from reaching several major markets.",
    "Customs officials will now require pre-shipment inspection certificates for any avionics component leaving the country.",
    "Chip substrate tariff hike rattles regional supply chains.",
    "A new round of tariffs targets imported chip-packaging materials.",
    "A revised customs code now applies to battery separators, subjecting them to an additional review before they can cross the border.",
    "The countries signed a memorandum easing restrictions on cross-border component trade, and aerospace fasteners are among the first goods to benefit from the streamlined customs process.",
    "Import tariffs on foreign-made lithography chemicals have been raised sharply.",
    "A newly signed accord removes the licensing step previously required before lithium salts could be shipped between the two countries.",
    "Export restrictions on aerospace-grade titanium alloys have been tightened by trade officials.",
    "Customs delays mount as new chip-chemical certificate rule kicks in.",
    "A bilateral agreement removes tariffs on battery components traded between the two markets.",
    "Cross-border shipments of navigation modules have slowed since customs began requiring a newly introduced compliance declaration.",
    "Any chip-grade polymer crossing the border will now be taxed at a rate double the previous level.",
    "New import duties on foreign aircraft components have been announced by the trade ministry.",
    "Border tax added to imported cathode precursor.",
    "A trade dispute has led to retaliatory tariffs on semiconductor testing equipment.",
    "Shipping a completed landing-gear assembly across the border now requires sign-off from two separate customs agencies instead of one.",
    "Sanctions have cut off a lithium producer's access to several export markets.",
    "The finance ministry unveiled a revised customs schedule this week, and chip-grade ceramics will now face a new border levy when entering the country.",
    "A new trade pact lowers duties on cross-border aerospace component shipments.",
    "Customs backlog builds as new battery-material certificate rule begins.",
    "A revised bilateral accord will remove the licensing step currently required before chip-testing equipment can be shipped across the border.",
    "Tariffs on imported avionics parts have been raised as part of a broader trade dispute.",
]

# ---------------------------------------------------------------------------
# QUOTA_CHANGE (50)
# ---------------------------------------------------------------------------
quota_change = [
    "The export quota for rare-earth materials has been cut by 15 percent for the coming year.",
    "No more than 40,000 wafers may leave the country's ports each month under new guidance issued this week.",
    "Overseas lithium allocation shrinks by a third.",
    "The government has set a new annual limit of 5,000 tonnes on titanium sponge exports.",
    "Buyers abroad will be limited to a fixed tonnage of polysilicon each quarter, industry sources confirm, down sharply from current levels.",
    "The cobalt export allowance has been increased from 30,000 to 45,000 tonnes annually.",
    "The materials board met twice this month to review overseas allocations, and aerospace-grade titanium shipments will now be held to a fixed ceiling of 8,000 tonnes a year.",
    "A production quota has been introduced limiting how much polysilicon a single plant may output monthly.",
    "Graphite shipments capped at 60,000 tonnes annually.",
    "Only 500 units of the flight-control module may leave the country each month under updated allocation guidance.",
    "The government has reduced the annual gallium export quota by 20 percent.",
    "Cell makers overseas say their planned imports have been slashed after the exporting country capped annual shipments at half of last year's volume.",
    "A ceiling of 2,000 tonnes has been placed on annual exports of the specialty alloy used in turbine blades.",
    "Maximum production limits for a key chipmaking chemical have been established by regulators.",
    "Nickel allocation to shrink for third straight year.",
    "The export allowance for aerospace-grade carbon fiber has been raised from 10,000 to 14,000 tonnes.",
    "Overseas shipments of a specialty etching gas will be held to 1,200 tonnes this year, roughly half of what was allowed twelve months ago.",
    "The ministry finished its annual review of critical-mineral exports, and producers will now be restricted to shipping no more than 100,000 tonnes of spodumene concentrate abroad this year.",
    "A new quota limits silicon carbide wafer exports to 25,000 units per quarter.",
    "Titanium sponge export ceiling lowered for second year running.",
    "The annual manganese export quota has been reduced by a quarter.",
    "Foreign buyers will be able to purchase no more than a fixed share of the country's neon gas output starting this quarter, down from unrestricted access previously.",
    "The materials authority set a hard limit of 3,500 tonnes on titanium billet exports for the year ahead.",
    "Export allowances for high-purity silicon have been cut in half.",
    "Cathode-grade nickel allocation trimmed by a fifth.",
    "Buyers say their orders have been rationed since the exporting nation set a fixed annual cap on rare-earth magnet shipments.",
    "The permitted volume of gallium exports has been reduced for the second consecutive year.",
    "Shipments of processed cobalt will be restricted to a set tonnage each month, roughly two-thirds of the previous pace.",
    "Connector-grade rare-earth exports face new annual cap.",
    "A quarterly export cap on specialty photoresist chemicals has been introduced.",
    "The country will allow no more than 90,000 tonnes of refined lithium carbonate to leave its ports next year, down from an uncapped total previously.",
    "The trade bureau finalized new export tables this week, and germanium shipments abroad will now be capped at 600 tonnes annually, a steep drop from recent years.",
    "The export limit on aircraft-grade aluminum alloys has been raised by a third.",
    "Spodumene export cap set well below last year's shipments.",
    "A new annual ceiling of 15,000 tonnes has been placed on exports of high-purity quartz.",
    "A fixed monthly allocation will now govern how much aerospace-grade titanium may be shipped to any single buyer.",
    "The number of advanced packaging substrates a single buyer may import each quarter will now be capped at a set figure, down from no limit at all.",
    "The government has doubled the annual export allowance for battery-grade nickel sulfate.",
    "Rare-earth magnet allocation for aerospace buyers cut sharply.",
    "A production ceiling has been set on monthly polysilicon output for domestic plants.",
    "Overseas buyers have begun rationing existing stock after the producing country fixed graphite exports at a fraction of last year's total.",
    "Industry groups had lobbied for looser limits ahead of the review, but the board set next year's titanium export ceiling below even this year's reduced level.",
    "Export quotas for tantalum capacitor materials have been tightened.",
    "Battery-grade cobalt shipments held to fixed annual figure.",
    "A hard cap of 6,500 tonnes will apply to exports of a specialty semiconductor-grade gas starting next quarter.",
    "The permitted export volume of specialty aerospace resins has been increased by 40 percent.",
    "No more than 70 percent of last year's lithium hydroxide export volume will be allowed to leave the country this year.",
    "A strict output cap now limits how much gallium a single refiner may produce each month.",
    "Fixed shipment ceiling introduced for specialty aerospace alloys.",
    "Buyers overseas will receive a fixed allotment of high-purity silicon each quarter, replacing the previously unlimited purchase arrangement.",
]

# ---------------------------------------------------------------------------
# Assemble, validate, shuffle, and write
# ---------------------------------------------------------------------------
label_map = {
    "SUPPLY_DISRUPTION": supply_disruption,
    "REGULATION_CHANGE": regulation_change,
    "FACILITY_OUTAGE": facility_outage,
    "TECHNOLOGY_EMBARGO": technology_embargo,
    "TRADE_POLICY_CHANGE": trade_policy_change,
    "QUOTA_CHANGE": quota_change,
}

allowed_labels = {
    "SUPPLY_DISRUPTION", "REGULATION_CHANGE", "FACILITY_OUTAGE",
    "TECHNOLOGY_EMBARGO", "TRADE_POLICY_CHANGE", "QUOTA_CHANGE",
}
assert set(label_map.keys()) == allowed_labels, "Label set mismatch!"

for label, items in label_map.items():
    assert len(items) == 50, f"{label} has {len(items)} items, expected 50"

records = []
for label, items in label_map.items():
    for text in items:
        records.append({"text": text.strip(), "label": label, "source": "synthetic"})

assert len(records) == 300, f"Expected 300 records, got {len(records)}"

texts = [r["text"] for r in records]
dupes = [t for t, c in Counter(texts).items() if c > 1]
assert len(dupes) == 0, f"Duplicate text(s) found: {dupes}"

for r in records:
    assert r["label"] in allowed_labels
    assert r["source"] == "synthetic"
    assert len(r["text"]) > 0

random.seed(42)
random.shuffle(records)

final_records = []
for i, r in enumerate(records, start=1):
    final_records.append({
        "id": f"syn_{i:06d}",
        "text": r["text"],
        "label": r["label"],
        "source": r["source"],
    })

ids = [r["id"] for r in final_records]
assert len(ids) == len(set(ids)), "Duplicate IDs found!"
assert ids == sorted(ids), "IDs not sequential!"

out_path = "data/event_classifier/candidates/synthetic_300.jsonl"
with open(out_path, "w", encoding="utf-8") as f:
    for rec in final_records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

label_counts = Counter(r["label"] for r in final_records)
print("=== VALIDATION REPORT ===")
print("Total records:", len(final_records))
print("Label counts:", dict(label_counts))
print("Unique texts:", len(set(r["text"] for r in final_records)), "/", len(final_records))
print("Unique ids:", len(set(ids)), "/", len(ids))
print("First id:", final_records[0]["id"], " Last id:", final_records[-1]["id"])
print("All sources synthetic:", all(r["source"] == "synthetic" for r in final_records))
print("All labels allowed:", all(r["label"] in allowed_labels for r in final_records))

# soft check: repeated 3-word openings (informational only)
openings = Counter(" ".join(r["text"].split()[:3]) for r in final_records)
repeated = {k: v for k, v in openings.items() if v >= 3}
print("Openings (first 3 words) repeated 3+ times:", repeated if repeated else "none")

# length distribution (word count) informational
lengths = [len(r["text"].split()) for r in final_records]
print("Text length (words) min/avg/max:", min(lengths), round(sum(lengths)/len(lengths), 1), max(lengths))

print("=== DONE, wrote:", out_path, "===")
