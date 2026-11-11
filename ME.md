PublishedasaconferencepaperatICLR2026
| MOBIEDIT: |     |                  | RESOURCE-EFFICIENT |     |           |     | KNOWLEDGE |
| --------- | --- | ---------------- | ------------------ | --- | --------- | --- | --------- |
| EDITING   |     | FOR PERSONALIZED |                    |     | ON-DEVICE |     | LLMS      |
ZhenyanLu1,2,DaliangXu1,DongqiCai1,4,ZexiLi5,6,WeiLiu7,FangmingLiu*2,
ShangguangWang1,MengweiXu*1,3
1BeijingUniversityofPostsandTelecommunications,2PengchengLaboratory,
3BeiyouShenzhenInstitute,4NanjingUniversity,5TheChineseUniversityofHongKong,
6KnowinAI,7IndependentResearcher
ABSTRACT
|     | Large language | models | (LLMs)         | are deployed | on   | mobile devices | to power killer    |
| --- | -------------- | ------ | -------------- | ------------ | ---- | -------------- | ------------------ |
|     | applications   | such   | as intelligent | assistants.  | LLMs | pre-trained    | on general corpora |
oftenhallucinatewhenhandlingpersonalizedorunseenqueries,leadingtoincor-
|     | rectoroutdatedresponses. |     |     | Knowledgeeditingaddressesthisbyidentifyingand |     |     |     |
| --- | ------------------------ | --- | --- | --------------------------------------------- | --- | --- | --- |
adjustingasmallcrucialportionofmodelweights,withoutcompromisingthegen-
eralknowledge.However,priorknowledgeeditingmethodsareimpracticaltorun
onlocaldevicesduetotheresource-heavybackpropagation(BP)neededforup-
dates.WepresentMobiEdit1,thefirstmobileknowledgeeditingframeworkthat
|     | enables      | efficient LLM                                             | personalization | on  | commercial | off-the-shelf | (COTS) mo- |
| --- | ------------ | --------------------------------------------------------- | --------------- | --- | ---------- | ------------- | ---------- |
|     | biledevices. | MobiEditreplacesfull-precisionBPwithquantizedforward-only |                 |     |            |               |            |
gradientestimation,thuscompatiblewiththeenergy-efficientmobileneuralpro-
|     | cessingunits(NPUs).   |     | Tofurtherimprovegradientestimationefficiency,weintro- |     |     |     |     |
| --- | --------------------- | --- | ----------------------------------------------------- | --- | --- | --- | --- |
|     | ducetwooptimizations: |     | anearlystoppingmechanismthatadaptivelyterminates      |     |     |     |     |
editinguponsuccessandprefixactivationreusingthatreduceredundantcomputa-
|     | tionacrosssteps.     | Ourapproachenablesreal-timeeditingof3B-parametermodels |     |                       |     |         |                     |
| --- | -------------------- | ------------------------------------------------------ | --- | --------------------- | --- | ------- | ------------------- |
|     | (Qwen2.5-3B-Instruct |                                                        | and | Llama3.2-3B-Instruct) |     | on COTS | mobile devices with |
7.1×lessmemory,15.8×lessenergyand3.4×lesslatencycomparedtoprevious
knowledgeeditingmethods.
1 INTRODUCTION
Mobile LLMs are transitioning from research to real-world deployment, empowering privacy-
preserving and latency-sensitive applications such as personal agents (Apple (2024); Li et al.
(2024)).WhilemobileLLMsalreadyembedgeneralworldknowledge,apersonalizedknowledgeis
crucialforbetterunderstandingindividualusers. Thisuser-specificinformationistypicallyabsent
ordilutedduringpre-trainingonlargepublicdatasets. AsFigure1shows, iftheuserprovidesthe
address in one conversation, personalized LLM assistant memorizes the address and applies this
informationtothefuturerequest.
To achieve such personalization, several approaches have been explored in LLMs, including
retrieval-augmentedgeneration(RAG)(Fanetal.(2024)),fine-tuning,andknowledgeediting(Wang
et al. (2024b)). RAG expands prompts by retrieving external knowledge without changing model
parameters. However, it adds inference overhead and relies heavily on strong in-context learning
capabilities,whicharetypicallyweakinsmallLLMsdeployedonmobiledevices(Luetal.(2024)).
Fine-tuning requires a large number of training samples for each target fact. It updates model pa-
rameterswithhighcomputationalcostandfaceschallengesincollectingsufficientdataon-device.
Incontrast,knowledgeeditingmodifiesonlyasmallsubsetofparameterstoinjectnewknowledge.
It maintains high inference speed and can incorporate a single fact with just one training sample.
These characteristics make it well-suited for resource-constrained mobile environments. A pre-
vailingknowledgeeditingparadigmisthelocate-and-editapproach(Daietal.(2022);Mengetal.
(2022;2023);Guetal.(2024);Fangetal.(2025)),whichfirstidentifiesinfluentialparametersand
1Theprojectisreleasedathttps://github.com/UbiquitousLearning/MobiEdit.
1

PublishedasaconferencepaperatICLR2026
thenmodifiesthembyintroducingaperturbationoptimizedthroughbackpropagationtoproducethe
expectedoutput.
| Firstchat         |     |                     | MobiEdit                     |     | Secondchat        |
| ----------------- | --- | ------------------- | ---------------------------- | --- | ----------------- |
|                   |     | NPU-friendly        | BP-Free Model Editing (§2.2) |     |                   |
| Whatismyaddress ? |     | Training stage      |                              |     |                   |
|                   |     |                     |                              | key | Whatismyaddress ? |
|                   |     | Quantization (§2.3) | Compute the subject key      |     |                   |
Sorry, I don’t have
related information.
|                         |               | Model              | F o r w a r d   P a ss   w it h                 | C o m p u t e   t h e     | Y o u r  a d d r es s   i s        |
| ----------------------- | ------------- | ------------------ | ----------------------------------------------- | ------------------------- | ---------------------------------- |
|                         |               |                    |                                                 | ne w   W d o w n _ p ro j | N o .1 0 1 0 ,  B e ij i n g Road. |
|                         |               |                    | P re f ix   A c t iv a ti o n   R eusing (§2.4) |                           | After                              |
| My address is No.1010,  |               |                    |                                                 |                           | Editing                            |
| Beijing Road.           |               | Mix -p re c i sion |                                                 | value                     |                                    |
|                         | Use-specific  | M o d e l          | Early Stopping (§2.4)                           |                           |                                    |
Information
|     | Inject |     |                   |     | OnCPU |
| --- | ------ | --- | ----------------- | --- | ----- |
|     |        |     | update Wdown_proj |     | OnNPU |
Figure1: Theon-deviceLLMremembersuserinformationfromthefirstinteractionandappliesit
tosubsequentrequests.
Despite being effective in updating model knowledge, current knowledge editing methods relying
onbackpropagation(BP)facethreecriticalchallengesformobiledeployment: (1)Incompatibility
withforwardoperatorsonmobileNPUs. Modernsmartphonesareequippedwithhigh-performance
and energy-efficient NPUs, such as Google edge TPU and Qualcomm Hexagon. These NPUs are
designedandoptimizedprimarilyforLLMinference,providingupto60×speedupoverCPUs(Xu
etal.(2025)). However, training-specificoperationsareoftenunsupportedorpoorlyoptimizedon
mobileNPUs(Xuetal.(2024)),renderingBP-basedknowledgeeditingmethodsinfeasibleinprac-
tice. (2) Poor quantization support. BP-based training operations are often unstable or ineffective
on fully quantized models (§2.3). This lack of quantization support exacerbates the previous two
challenges: the memory footprint of model parameters remains prohibitively large because full-
precisionweightsmustbestoredandupdated,anditpreventsefficientexecutiononmobileNPUs,
whicharespecificallyoptimizedforlow-bitintegercomputation. (3)Substantialmemoryoverhead.
Forexample,editinga3B-parameterLLM(Qwen2.5-3B-Instruct)usingtheclassiclocate-and-edit
methodROME(Mengetal.(2022))requiresover40GBofmemorytoboththefull-precisionmodel
andactivationsforBP,whichfarexceedsthememorycapacityofsmartphones,typicallylessthan
16GB.
Theabovechallengesconfinecurrentknowledgeeditingmethodstocloud-basedcomputation,un-
derminingtwokeyadvantagesofmobileLLMs:privacypreservationandofflineavailability. Inthis
paper, we propose MobiEdit, the first mobile knowledge editing system for efficient LLMs per-
sonalization. MobiEdit is designed to be memory-efficient, NPU-friendly, and compatible with
quantization,targetingpracticaldeploymentonresource-constrainedCOTSmobiledevices.
Our solution. To unleash the power of mobile NPUs, MobiEdit builds atop ROME, a widely
used locate-and-edit scheme, with a few key building blocks renovated: (1) BP-free training. In-
stead of calculating standard gradients using BP, MobiEdit uses zeroth-order optimization ap-
proach to estimate the gradients. MobiEdit operates entirely through forward passes, which
is memory-efficient and well-suited for mobile NPUs. (2) NPU-friendly training stage quantiza-
tion. MobiEdit introduces a new quantization paradigm for efficient knowledge editing on mo-
bileNPUs. UnlikepreviousBP-basedlow-precisiontraining,ourforward-onlygradientupdatingis
morestableunderquantizedcomputation.Wetherebyquantizeallmodelparametersexceptthecrit-
icalprojectionweightsessentialtoknowledgeediting. Onlyasmallportionofweightsundergoes
full-precisioncomputationtoconductprecisegradientestimation. (3)ThecombinationofBP-free
trainingandNPU-friendlyquantizationfurtherreducesmemoryconsumption. Withouttheneedfor
backpropagation,activationsarenotstored,andonlyINT8-quantizedweightsaremaintained.
We introduce two optimizations to further improve system efficiency: a prefix activation reusing
thatstoresKVcacheandMLPactivationsacrosseditingsteps,andanearlystoppingthatadaptively
terminates editing once success criteria are met for different knowledge. Together, these design
choicesmakeMobiEditefficientandpracticalformobiledeployment.
Results. We test our method on three COTS mobile phones, Redmi K60 Pro, Redmi K70 Pro
and OnePlus 13. On the ZsRE and CounterFact datasets, MobiEdit achieves comparable edit
2

PublishedasaconferencepaperatICLR2026
quality while reducing memory usage by 7.1×, editing latency by 3.4×, and energy consumption
by15.8×comparedtodifferentknowledgeeditingmethods,ROME(Mengetal.(2022)),MEMIT
(Mengetal.(2023)),WISE(Wangetal.(2024a)),andAlphaEdit(Fangetal.(2025)). Toourbest
knowledge,MobiEditisthefirstsystemtomakeLLMknowledgeeditingfeasibleoncommercial
smartphones.
2 METHOD
2.1 MOBIEDIT OVERVIEW
Locate-and-edit methods (e.g., ROME, MEMIT) formulate knowledge editing as updating the
key–value memory in the MLP layers of LLMs: the subject token is mapped to a key k , and a
∗
value v vector representing the target fact is optimized, after which the weight matrix is updated
so that Wk = v. This paradigm is effective for accuracy and locality, but existing methods rely
∗
onmulti-stepbackpropagationtoobtainv,whichleadstolargememoryfootprintandhighlatency,
renderingtheminfeasibleonforward-onlyNPUsandresource-constrainedmobiledevices.
MobiEdit inherits this locate-and-edit formulation but present a complete algorithm–hardware
co-designedsystemtoenablepracticalon-devicedeployment(Figure1). Specifically,MobiEdit
performseditsinthreecoordinatedstages:
(1) NPU-friendly training stage quantization, converting the original model into a mixed-
precisionformatalignedwithmobileNPUconstraints;
(2) BP-Free model editing, replacing the backpropagation-based optimizer with a forward-only
gradientestimator,furtherenhancedbyprefixactivationreusingandearlystopping;
(3) Model update, applying the optimized value vector to modify the mixed-precision model in-
place,sothatsubsequentinteractionscanimmediatelybenefitfromtheinjectedknowledge.
Insummary,MobiEditretainstheeffectivekey–valueeditingparadigmwhilereplacingitsback-
propagationwithalightweightforward-onlyworkflow,augmentedbyquantizationandsystem-level
optimizationsformobileNPUs.
2.2 BP-FREEKNOWLEDGEEDITING
Unlike traditional methods that minimize this loss using backpropagation-based gradients,
MobiEdit estimate the gradients using only forward passes. Specifically, we employ a central-
difference estimator along sampled perturbation directions. Given a perturbation direction u ∼
N(0,I),thedirectionalgradientestimateiscomputedas(Baydinetal.(2022)):
L(W +µu)−L(W −µu)
∇(cid:98)v L=
2µ
·u, (1)
whereµ>0isasmallscalarstepsize. Tofurtherreducevarianceandstabilizetraining,weaverage
overN independentlysampleddirectionsu ∼N(0,I):
i
N
∇(cid:98)v L=
N
1 (cid:88)L(v+µu
i
)
2
−
µ
L(v−µu
i
)
·u
i
. (2)
i=1
Wethenupdatethevaluevectorasv ← v−η∇(cid:98)v L, whereη isthelearningrate, andrepeatuntil
convergence.Thisprocedureperformsapproximategradientdescentusingonlyforwardevaluations.
Weapplythisprocessiterativelytoupdatev. Oncetheoptimalv∗ isobtained,weapplyaclosed-
formrank-oneweightupdate:
v∗−Wk
W(cid:99) =W +Λ(C−1k
∗
)⊤, where Λ=
(C−1k )⊤k
∗ . (3)
∗ ∗
Here C = KK⊤ is the estimated key covariance matrix, computed from a sample of key vectors
extractedfromthemodel’sactivationstatistics. Thisupdateeffectivelyinsertsthepair(k ,v∗)into
∗
theMLP’skey-valuememory,enablingthemodeltorecallthenewfactualassociation.
3

PublishedasaconferencepaperatICLR2026
INT8
INT16 INT16 FP32 FP32
gate_proj
xi dequantize down_proj edit quantize
up_proj FP32 FP32 FP32 INT16
INT16 INT16
INT8 floatoperators intoperators updatedoperators
Figure 2: MobiEdit quantization workflow and strategy. MobiEdit applies quantization to all
activations,whileretainingfloating-pointprecisiononlyfortheeditinglayeranditsprecedinglayer.
Benefits of BP-free editing. BP-free editing is well-suited for mobile NPUs that only support
forwardpasses. Intermsofmemoryefficiency,activations,whichtakemorethan40%ofBP-based
memoryconsumption,canbeinvalidatedimmediatelyaftertheforwardpass,becauseonlythefinal
outputisrequiredtocomputetheestimatedgradients.
2.3 NPU-FRIENDLYTRAININGSTAGEQUANTIZATIONFORBP-FREEEDITING
Although activations no longer need to be stored, the large size of LLM weights can still exhaust
the memory capacity of mobile devices. A 3B-parameter model, such as Qwen2.5-3B-instruct,
requires about 12 GB of full-precision weights. While the newest COTS mobile devices, such as
theXiaomi15,typicallyhave16GBofRAM,onlyaround75%ofthisisavailableforapplications,
leavingroughly12GBusable. Asaresult,loadingthemodelalonecanexhaustavailablememory
andleadtofrequentout-of-memory(OOM)errors.
Besides,mobileNPUsarebestsuitedforacceleratingINTmatrixmultiplicationwith1024-bitINT8
vector arithmetic. Their floating-point computation capabilities are relatively weak compared to
mobile GPUs. To avoid frequent memory swapping, which can severely shorten the lifespan of
mobileSSDs,andtoleveragethecomputationaladvantagesofNPUs,weproposeanNPU-friendly
quantizationworkflowforBP-freeediting.
Quantization workflow and strategy. Figure 2 illustrates the quantization workflow of
MobiEdit. DuetothehardwareconstraintsofmobileNPUs,MobiEditemploysastaticquanti-
zationstrategy. Thestaticscalesforquantizationaredeterminedusingrepresentativecorporadata.
To balance efficiency and accuracy, MobiEdit adopts a mixed-precision editing approach: the
editing vector and its preceding linear layer are executed in floating-point format; while all other
weights are quantized to 8/16-bit integers. This design is informed by two key observations: (i)
MobiEdit modifies only a small set of parameters proportional to the hidden size. Even minor
quantizationerrorsinthiscontextcansignificantlyimpacteditingaccuracy. Furthermore,sincethe
editing module modifies the knowledge stored in its preceding linear layer (Meng et al. (2022)),
floating-point precision in this layer is also crucial to maintain accuracy. (ii) The edited vector,
being of limited size (equal to the hidden size), results in a negligible computational cost when
floating-pointprecisionisusedfortheeditingmoduleanditsprecedinglinearlayer. Forexample,
intheQwen-2.5-3Bmodel,thesecomputationsaccountforonly0.89%oftheoverallcomputation,
makingtheperformanceoverheadofusingfloating-pointprecisionminimal.
Advantageofourquantization. MobiEditismorerobusttoquantization-inducederrorsthan
backpropagation(BP)-basededitingmethods. ConsideranL-layerTransformernetworkwhereall
weightsandactivationsarefullyquantized:
Wq =W +ϵ , aq =a +ϵ , (4)
ℓ ℓ W,ℓ ℓ ℓ a,ℓ
where Wq and aq are the quantized weights and activations of the ℓ-th layer, and ϵ and ϵ
ℓ ℓ W,ℓ a,ℓ
denotezero-meani.i.d. quantizationerrorswithvarianceσ2,independentacrosslayersandforward
passes. Ineachforwardpass,quantizationnoiseaccumulatesrecursively.
Withoutlosinggenerality,wetakealinearfunctionf (x)=xasanintuitiveexampletoanalyzethe
ℓ
noiseaccumulationphenomenon,thenwehave:
L L
(cid:88)(cid:16) (cid:89) (cid:17)
aq =W W ···W x+ W ϵ , (5)
L L L−1 1 k j
j=1 k=j+1
4

PublishedasaconferencepaperatICLR2026
whereϵ representsthecombinedquantizationerroratlayerj. Consequently,thetotalvarianceof
j
theoutputnoiseis
|     |        |     | L        | (cid:13) L        | (cid:13)2            |     |     |     |
| --- | ------ | --- | -------- | ----------------- | -------------------- | --- | --- | --- |
|     | Var[aq |     | (cid:88) | (cid:13) (cid:89) | (cid:13) σ2 ∼O(Lσ2), |     |     |     |
|     |        | −a  | L ]=     |                   | W k(cid:13)          |     |     | (6) |
|     |        | L   |          | (cid:13)          |                      |     |     |     |
|     |        |     | j=1      | k=j+1             |                      |     |     |     |
whichgrowsonlylinearlywithnetworkdepthL.
Backpropagation further amplifies this noise via the chain rule. For a small edit ∆ in layer ℓ, the
gradientis:
|     |     |     |     | (cid:16) L  | (cid:17) ∂L |     |     |     |
| --- | --- | --- | --- | ----------- | ----------- | --- | --- | --- |
|     |     |     | gBP | (cid:89) W⊤ |             |     |     |     |
|     |     |     | =   |             | .           |     |     | (7) |
|     |     |     | ℓ   |             | j ∂a        |     |     |     |
L
j=ℓ+1
Since the weights themselves are quantized, each term in this product carries quantization noise.
Thevarianceofthegradientnoisethereforebecomes
(cid:89) L
|     | Var[gBP]=σ2 |     |     | ∥2      | (cid:0) σ2· ∥W∥2(L−ℓ) |     | (cid:1) |     |
| --- | ----------- | --- | --- | ------- | --------------------- | --- | ------- | --- |
|     |             |     |     | ∥W j ∼O |                       |     | ,       | (8) |
ℓ
|     |     |     | j=ℓ+1 |     | (cid:124) | (cid:123)(cid:122) | (cid:125) |     |
| --- | --- | --- | ----- | --- | --------- | ------------------ | --------- | --- |
exponentialindepth
indicating that deeper networks lead to an exponential escalation of noise, in sharp contrast to the
lineargrowthinforwardpropagation.
It is worth noting that in quantization-aware training (QAT) (Jacob et al. (2018)), the
Straight-ThroughEstimator(STE)(Courbariauxetal.(2016))avoidslayer-wiseerroraccumulation
bycomputinggradientsonfloatmasterweightswhiletreatingfakequantizationasidentity. Thisis
reasonable in QAT, as the goal is to update float weights before re-quantization. In our on-device
setting, weights are already quantized, with no float copy or fake quantization; both forward and
backwardpassesoperatefullyinthequantizeddomain. Here,quantizationerrorsstillaccumulatein
theforwardpass,andBP-basededitingfurthercompoundsthemexponentially.
In contrast to backpropagation, MobiEdit only accumulates noise during the forward pass. The
zeroth-ordergradientisestimatedviathecentereddifference:
|     |     |     |     | L ∆ −L | −∆, |     |     |     |
| --- | --- | --- | --- | ------ | --- | --- | --- | --- |
|     |     |     | gZO | =      |     |     |     | (9) |
|     |     |     | ℓ   | 2∆     |     |     |     |     |
L L
where ∆ and −∆ are the losses obtained from two independent forward passes with perturbed
weightsWq±∆.Eachforwardpassincursthesameforward-onlyquantizationerrorderivedabove,
ℓ
| withvarianceVar | ∼O(Lσ2). | Consequently,thevarianceoftheZOestimatoris |     |     |     |     |     |     |
| --------------- | -------- | ------------------------------------------ | --- | --- | --- | --- | --- | --- |
fw
|           |     | Var[L | ]+Var[L |     | ] 2Var |                          |     |      |
| --------- | --- | ----- | ------- | --- | ------ | ------------------------ | --- | ---- |
| Var[gZO]= |     |       | ∆       | −∆  | = fw   | ∼O (cid:0) Lσ2/∆2(cid:1) | ,   | (10) |
ℓ
|     |     |     | (2∆)2 |     | 4∆2 |     |     |     |
| --- | --- | --- | ----- | --- | --- | --- | --- | --- |
whichgrowsonlylinearlyindepthL,insharpcontrasttotheexponentialdependenceofbackprop-
agationandexplainingwhyMobiEditismorerobustindeepquantizednetworks.
QuantizationrobustnessevaluationofBP-freetraining.OurexperimentsinTable1demonstrates
thefragilityofBP-basededitingunderquantizationandtherobustnessofzeroth-orderoptimizations.
ROME’s editing success rate drops sharply from 96% in the FP32 setting to 41% in the W8A16
settingduetohighgradientnoiseinlow-bitconditions. Incontrast,MobiEditachievesascoreof
80underthesameW8A16quantization,demonstratingsubstantiallyhigherrobustness.
2.4 FURTHEROPTIMIZATIONS
Although a single step of MobiEdit is efficient on mobile NPUs, a remaining challenge is that
it requires significantly more steps to reach comparable convergence performance. Each gradient
estimateinzeroth-orderoptimizationistakenalongasingleperturbationdirection,causingdeviation
from the true gradient and requiring many more steps to reach stable convergence. For example,
MobiEdit requires on average 20× more steps than BP-based model editing on the ZsRE and
CounterFactdatasets,whicheliminatesitsefficiencyadvantageintermsofwall-clocktime.
5

PublishedasaconferencepaperatICLR2026
|     |     |     | )raB( egnaR petS ni noitroporP 0.40 |     | )eniL( noitroporP evitalumuC |
| --- | --- | --- | ----------------------------------- | --- | ---------------------------- |
11..0000 1.0
0.35 ZsRE
| Table1:Impactofquantizationoneditsuccessfor |     |     | CounterFact |     |     |
| ------------------------------------------- | --- | --- | ----------- | --- | --- |
|                                             |     |     | 0.30        |     | 0.8 |
ROME(BP)andMobiEdit(BP-Free).
0.25 00..6625
|     |     |     |     | 00..5562 | 0.6 |
| --- | --- | --- | --- | -------- | --- |
0.20
| Method | Precision EditSuccessScore |     | 0.15 0.38 | 0.40 | 0.4 |
| ------ | -------------------------- | --- | --------- | ---- | --- |
0.28
|          |      |     | 0.10 0.26 |     |     |
| -------- | ---- | --- | --------- | --- | --- |
| ROME(BP) | FP32 | 96  |           |     | 0.2 |
0.05 00..1006
| ROME(BP) | W8A16 | 41  |      |     |     |
| -------- | ----- | --- | ---- | --- | --- |
|          |       |     | 0.00 |     | 0.0 |
MobiEdit(BP-Free) FP32 86 <100 100-200200-300300-400400-500500-600
Step
| MobiEdit(BP-Free) | W8A16 | 80  |                        |            |           |
| ----------------- | ----- | --- | ---------------------- | ---------- | --------- |
|                   |       |     | Figure 3: Distribution | of editing | steps for |
successfuledits.
Earlystopping. Toaddressthis,wefirstanalyzethesuccessfuleditingstepdistributionofedited
facts. AsshowninFigure3,wefindthatdifferentknowledgehasdifferenteditingdifficulty. Based
onthisobservation,weintroducealightweightearlystoppingmechanismthatadaptivelydetermines
theeditinghorizonbasedonruntimesuccessfeedback. Specifically,duringediting,weperiodically
evaluate the model’s response to the edited fact every M steps (e.g., every 20 steps). The editing
process is terminated early once the model satisfies a pre-defined success criterion. This typically
occurs when it produces the desired target output with a confidence above a given threshold m.
Theearlystoppingmechanismautomaticallyadjuststheeditingstepstothecomplexityofeachedit
instance,avoidingunnecessaryforwardpassesforeasy-to-editfactsandreducingoverfittingriskby
stoppingatthepointoffirstsuccess.
Prefixactivationreusing. Inourknowledgeeditingsetting,eachoptimizationstepusesthesame
setofinputexamplesconstructedbycombiningafixedsetofrandomlysampledprefixeswiththe
| facttobeedited. Formally,foratargetfactf,wedefineasetofeditinginputsas: |                                      |                   |       |     |      |
| ----------------------------------------------------------------------- | ------------------------------------ | ----------------- | ----- | --- | ---- |
|                                                                         | X ={[p                               | +f],[p +f],...,[p | +f]}, |     | (11) |
|                                                                         | edit                                 | 1 2               | n     |     |      |
| wherep ,p ,...,p                                                        | aredifferentrandomlysampledprefixes. |                   |       |     |      |
| 1 2                                                                     | n                                    |                   |       |     |      |
Weobservethatineachstep, theprefixtokensintheinputdonotchange, andthereforetheircor-
responding activations are recomputed redundantly. To reduce this overhead, we introduce Prefix
activation reusing: during the first step, we cache the intermediate activations for the prefix to-
kens,andinallsubsequentsteps,thesecachedactivationsareinheritedacrosseditingstepswithout
recomputation, while only the fact tokens are recomputed. This greatly reduces compute without
changingthemodelarchitectureorinputformat.
Reusing ”stale” activations from previous steps introduces an accuracy-efficiency trade-off. We
observe this effect in Figure 5, which visualizes the ”staleness” by showing the cosine similarity
of activations between consecutive steps. While the similarity is high in many layers, it gradually
decreasesinothers,especiallyaseditingprogresses,indicatingthatthecachedprefixrepresentations
arenotperfectlyalignedwiththeevolvingmodel.Thefullimplicationsofthistrade-off,particularly
underquantization,areanalyzedindetailinSection3.3.
Toavoidthestalenessaccumulatesfromhaltingtheeditingprocess,were-computetheprefixacti-
vationsaslongastheeditinglossdoesnotdecreaseby0.001over3steps.
3 EXPERIMENTS
3.1 SETUP
Baselines. We compare MobiEdit against four representative locate-and-edit methods:
ROME (Meng et al. (2022)), MEMIT (Meng et al. (2023)), AlphaEdit (Fang et al. (2025)), and
WISE (Wang et al. (2024a)). These methods follow the same paradigm of identifying key acti-
vations and injecting new knowledge into MLP layers, but differ in target granularity and update
mechanisms. ROMEperformssingle-layerediting. MEMITextendsittomulti-factscenarios. Al-
6

PublishedasaconferencepaperatICLR2026
phaEdit uses null-space projections for preservation, and WISE incorporates dynamic routing to
FFNsthatstorefacts.
Datasets and model. We evaluate MobiEdit on two standard datasets widely used in factual
knowledgeediting: ZsRE(Levyetal.(2017)),azero-shotrelationextractiondatasetderivedfrom
WikiRE, and CounterFact (Meng et al. (2022)), a curated benchmark of factual edits targeting
namedentities(e.g.,people,locations),withtruthandcounterfactualcontexts. Thesetwodatasets
jointly assess edit success (correctly producing the target knowledge), locality (preserving unre-
lated knowledge), and portability (applying the edited knowledge across contexts), the three key
metrics for knowledge editing. We use Qwen2.5-3B-Instruct (QwenTeam (2024)) and Llama3.2-
3B-Instruct(AI@Meta(2024))asourtargetmodels.
Table2: Devicesusedinexperiments.
Device SoC RAM NPU
RedmiK60Pro Snapdragon8Gen2 16GBLPDDR5 HexagonNPUV73
RedmiK70Pro Snapdragon8Gen3 16GBLPDDR5 HexagonNPUV75
OnePlus13 Snapdragon8Elite 24GBLPDDR5 HexagonNPUV79
Implementation details. To assess on-device feasibility, we run all editing procedures on three
COTSmobiledevices,asshowninTable2.Weperformallexperimentsusinglocalinferenceengine
mllm-npu(Xuetal.(2025))optimizedforNPUexecution. ThelatencyonCPUisobtainedbyrun-
ningonmobilephonesusingllm.c(karpathy(2013)). Weusememoryswappingwhilereachingthe
memorylimit. MobiEditusesW8A16quantization(INT8weights,INT16activations),aformat
widely supported by mobile NPUs and inference engines, ensuring compatibility and throughput.
Themetricofmemoryusageinthispaperisdefinedasthetotalmemoryrequired,assumingsuffi-
cientmemoryisavailable.Forasimplecomparison,thesystemefficiencyvaluesarefirstnormalized
totherange[40,100]usingmin-maxnormalization,andtheninverted.
3.2 END-TO-ENDPERFORMANCE
Memory Efficiency Memory Efficiency Memory Efficiency Memory Efficiency
100 100 100 100
80 80 80 80
Locality 60 Time Efficiency Locality 60 Time Efficiency Locality 60 Time Efficiency Locality 60 Time Efficiency
R M W A M h O E I o S p M M b E h E I i a T E E d d i i t t 40 R M A O h O u E p r M M h M E I a T e E t d h i o t d 40 40 40
Portability Energy Efficiency Portability Energy Efficiency Portability Energy Efficiency Portability Energy Efficiency
Edit Success Edit Success Edit Success Edit Success
(a)QwenonZsRE (b)QwenonCF (c)LlamaonZsRE (d)LlamaonCF
Figure 4: The comprehensive editing ability and performance comparison of knowledge editing
methodsontheZsREandCounterFactdatasets.
Overallresults. WecompareMobiEditagainstallbaselinesacrosssixdimensions: editsuccess,
locality,portability,timeefficiency,memoryefficiency,andenergyefficiency,asshowninFigure4.
TheresultsshowingthatMobiEditachievesabalanceofhighaccuracyandlowresourcecost.
OnQwen2.5-3B-Instructmodel,MobiEditachievesan80.1editsuccessscore,72.6localityscore,
and51.4portabilityscorewhilerequiringonly25.5minutes,0.018kJenergy,and6.2GBmemory.
OnLlama3.2-3B-Instructmodel,MobiEditachievesaneditsuccessscoreof88.3,localityscoreof
44.3,andportabilityscoreof38.3,whilerequiringonly23.1minutes,0.017kJenergy,and5.0GB
memory. Although slightly behind in quality, MobiEdit significantly outperforms in efficiency,
reducingmemoryusagebymorethan7×andenergyconsumptionbyover10×. Thesesubstantial
resourcesavingsmakeMobiEdittheonlyrealisticallyviablesolutionformobiledevices.
ThesignificantperformanceimprovementisattributedtoMobiEditleveragingaBP-freeediting
method, whichreducesthememoryandcomputationaloverheadcausedbybackpropagation. Ad-
ditionally, MobiEdit incorporates mobile hardware-friendly quantization and two optimizations
7

PublishedasaconferencepaperatICLR2026
specificallydesignedforthebp-freetrainingstep. Theseenhancementsnotonlymaximizetheper-
formance potential of mobile NPUs but also minimize the number of training steps and eliminate
redundantcomputations.
WithMobiEdit’sexceptionalperformancegains,althoughourmethod
hasadropineditaccuracy,itsignificantlyimprovesthenumberofsuc- Table 3: Facts edited
cessfuleditsperunittime,whichiscriticalforreal-worldusability.Since successfully within 8
knowledge editing occupies device resources and cannot be performed hours on Redmi K60
while the user is actively using their phone, in practice there are only Pro.
about 8 hours per day (e.g., when the user is asleep) available for edit-
ing. AsshowninTable3, in8hours, ourmethodcansuccessfullyedit
Method Count
14facts, whereastraditionalmethodsonlyaccomplish2–5. Forsimple
facts, ourmethodrequiresonly2–3minutes, whiletraditionalmethods ROME 5
incurafixedprocessingtimeofeither1.25hoursor3hoursforallfacts, MEMIT 5
WISE 2
depending on the specific method used. Running traditional methods
AlphaEdit 4
alsocausesatemperatureincreaseofapproximately10°Cafterjust100
MobiEdit 14
secondsofsustainedCPUload,resultingindevicelagorshutdown.
Editingperformance. Table4providesadetailedcomparisonofmem-
ory,latency,andenergyusageacrossthreecommercialsmartphonesonZsREdataset. Allbaseline
methodsconsideredinourexperiments,includingROME,MEMIT,AlphaEdit,andWISE,require
morethan30GBofmemory. Thisisduetothelackofmemoryoptimizationinllm.cfortraining
partparameters. Andtheirper-editenergyisrangingfrom0.18Jto0.36J.Forinstance,WISEcon-
sumes 0.36J and takes 11,359 seconds on K60 for a single edit. Such workloads not only exceed
memorybudgetsbutimposeintensethermalandschedulingpressureonmobilehardware.
• Qwen2.5-3B-Instruct. MobiEdit consumes only 6.2GB memory under 0.03J energy per edit
across all devices, completing edits in 1211 to 1902 seconds. This 10× energy reduction allows
MobiEdittoruneditingworkloadsunobtrusivelyinthebackgroundwithoutinterruptingtheuser
experienceortriggeringthermallimits. Suchsustainabilityiscriticalforreal-worldmobileapplica-
tions,whereknowledgeeditingmaybetriggeredinteractivelyundertightsystemconstraints.
•Llama3.2-3B-Instruct. MobiEdituses5GB,achieving3.1×to6.1×lowerlatencyand13.6×
to27.6×higherenergyefficiencythanbaselines.Theaveragelatencyis1411secondsonLlama3.2-
3B compared with 1530 seconds on Qwen2.5-3B, since Llama3.2 adopts a wider and shallower
architecture(3072×28vs.2048×36),beingmorecomputationallyfavorableforNPUs.
AppendixAandBdetailsthattheperformancegainscomefromouralgorithm–hardwareco-design:
(i) eliminating backward passes, (ii) using prefix activation reusing to cut redundant computation,
and(iii)aligningcomputationprecisionwithNPUcharacteristics.
3.3 ABLATIONSTUDY
OnLlama3.2-8B-Instruct,MobiEditachievesan85.3editsuccessscore. Ourablationstudyindi-
catesthatprefixactivationreusingisthemainsourceofthequalitytrade-off,reducingthesuccess
scoreby8.4points,whilequantizationhasamuchmilderimpact,withonlya2.1pointdrop.
Tounderstandwhyprefixreusinghassuchasignificantimpact,weprovideadetailedvisualanalysis
contrastingtheactivationdynamicsinFP32andquantizedsettings. First, inanidealFP32setting
as Figure 5a shown, we observed that activations are extremely stable, which provided the core
motivationforourprefixreusingoptimization. Asshownbelow,thesimilaritybetweenconsecutive
stepsisveryhigh(>0.90)formostlayers. However,aslightdecreaseinsimilaritycanstillbeseen
inthetopandbottomlayersovertime,illustratingthe”staleness”effect.
Second,wefoundthatquantizationsignificantlyamplifiesthisinstability. Figure5bshowstheanal-
ysisinourpracticalW8A16quantizationwithINT8weightsandINT16activations. Severallayers
now exhibit consistently low similarity (the dark horizontal bands), indicating significant volatil-
ity. Interestingly, these volatile layers are concentrated near the input and output of the network.
This aligns with observations in the quantization literature(An et al. (2025)), which find that out-
lierfeatures,akeychallengeforquantization,aremostprominentinthefirstandlastTransformer
layers. Quantizingtensorswithlargeoutliervaluesrequiresalargequantizationstepsize. Dueto
thislargestepsize,asmallperturbationtoapre-quantizedactivationvaluecaneasilycauseittobe
8

PublishedasaconferencepaperatICLR2026
Table4: Performancecomparison ofourmethodwithNPUandotherknowledge editingmethods
withCPUondifferentdevices.
(a)Qwen2.5-3B-Instruct
|     |     |     | K60 |     | K70 | OnePlus |     |
| --- | --- | --- | --- | --- | --- | ------- | --- |
Method Memory(GB)
|      |       | Time(s) | Energy(kJ) | Time(s) | Energy(kJ) | Time(s) | Energy(kJ) |
| ---- | ----- | ------- | ---------- | ------- | ---------- | ------- | ---------- |
| ROME | 46.14 | 4543.78 | 25.13      | 4276.49 | 24.23      | 3252.81 | 18.02      |
MEMIT
|           | 46.14 | 4543.78  | 25.13 | 4276.49 | 24.23 | 3252.81 | 18.02 |
| --------- | ----- | -------- | ----- | ------- | ----- | ------- | ----- |
| WISE      | 46.30 | 11359.44 | 63.82 | 8552.99 | 47.16 | 6505.63 | 36.05 |
| AlphaEdit | 46.14 | 4543.78  | 25.13 | 4276.49 | 24.23 | 3252.81 | 18.02 |
| MobiEdit  | 6.20  | 1902.88  | 0.023 | 1477.67 | 0.018 | 1211.83 | 0.014 |
(b)Llama3.2-3B-Instruct
|     |     |     | K60 |     | K70 | OnePlus |     |
| --- | --- | --- | --- | --- | --- | ------- | --- |
Method Memory(GB)
|           |       | Time(s) | Energy(kJ) | Time(s) | Energy(kJ) | Time(s) | Energy(kJ) |
| --------- | ----- | ------- | ---------- | ------- | ---------- | ------- | ---------- |
| ROME      | 34.14 | 4834.78 | 27.01      | 4578.66 | 25.23      | 3551.82 | 20.22      |
| MEMIT     | 34.14 | 4834.78 | 27.01      | 4578.66 | 25.23      | 3551.82 | 20.22      |
| WISE      | 35.05 | 9668.86 | 53.89      | 9157.32 | 50.45      | 6505.63 | 39.32      |
| AlphaEdit | 34.14 | 4834.78 | 27.01      | 4578.66 | 25.23      | 3551.82 | 20.22      |
| MobiEdit  | 5.06  | 1754.26 | 2.10       | 1362.26 | 1.71       | 1117.19 | 1.44       |
Table5: EditQualityComparisonforLlama3.2-8B-InstructonZsREdataset.
|     |     |     | ROME             | zo zo+prefix | zo+prefix+quan |     |     |
| --- | --- | --- | ---------------- | ------------ | -------------- | --- | --- |
|     |     |     | EditSucc 96.2    | 95.8 87.4    | 85.3           |     |     |
|     |     |     | Portability 51.3 | 50.6 33.2    | 38.3           |     |     |
|     |     |     | Locality 57.9    | 66.6 56.2    | 66.3           |     |     |
|     |     |     | Fluency 555      | 580 566      | 582            |     |     |
mapped to a different integer after quantization.This results in a large, discrete change in the final
quantized activation, even though the initial perturbation was small and continuous. This effect is
mostpronouncedinoutlier-richlayersandexplainsthesignificantdropinactivationsimilaritywe
observe.
Thiscomparativeanalysisdirectlyexplainsthesourceofthequalitytrade-off: itstemsfromacom-
poundingeffect. Ouroptimizationreusesactivationsthatarenotonlystalebutalsonoisyandim-
precise due to quantization. The interaction of these two factors leads to less accurate gradient
estimates. TobespecificonwhyPortabilityandLocalityarehurtmore: Thesetwometricsrequire
enough precision. Portability needs to update a semantic space for generalization. Locality needs
toisolatetheedittoavoiddamagingunrelatedfacts. Thegradientestimatedfromstale, quantized
activationsisslightlyblurry. WhileitisaccurateenoughtoensureEditSuccess,itlacksthesurgical
precisiontoperfectlyremapthesemanticspaceandpreventleaksintounrelatedknowledge.
| 4 RELATED | WORK |     |     |     |     |     |     |
| --------- | ---- | --- | --- | --- | --- | --- | --- |
Knowledge editing. Existing methods include locate-and-edit (ROME (Meng et al. (2022)),
MEMIT(Mengetal.(2023)),AlphaEdit(Fangetal.(2025)),WISE(Wangetal.(2024a))),which
directly modify model weights; retrieval-augmented (e.g., RECIPE (Chen et al. (2024))), which
fetchexternalknowledge;andmeta-learning(MEND(Mitchelletal.(2021))),whichlearnsediting
strategiesfromexamples. Lietal.(2025)improveseditingalgorithmsinunlearningsettings. While
having good editing quality, these approaches rely on multi-step backpropagation, leading to high
memory and latency. We instead target memory-efficient, NPU-friendly, quantization-compatible
editing.
BP-Free training. Zeroth-order methods such as FwdLLM (Xu et al. (2024)) and MeZO (Mal-
ladi et al. (2023)) estimate gradients via forward-pass perturbations and enable high-quality adap-
9

PublishedasaconferencepaperatICLR2026
|     | Query Similarity |     |     | Key Similarity |     |     | Value Similarity |     |     |
| --- | ---------------- | --- | --- | -------------- | --- | --- | ---------------- | --- | --- |
012345678901234567890123456789012345 1.000 012345678901234567890123456789012345 1.000 012345678901234567890123456789012345 1.00
|                            |     |     | 0.995                      |     |     | 0.995                            |     |     | 0.98 |
| -------------------------- | --- | --- | -------------------------- | --- | --- | -------------------------------- | --- | --- | ---- |
| 11111111112222222222333333 |     |     | 11111111112222222222333333 |     |     | 0.990 11111111112222222222333333 |     |     |      |
0.990
0.96
0.985
| reyaL |     |     | 0.985 reyaL |     |     | reyaL |     |     |      |
| ----- | --- | --- | ----------- | --- | --- | ----- | --- | --- | ---- |
|       |     |     |             |     |     | 0.980 |     |     | 0.94 |
0.980
|     |     |     |     |     |     | 0.975 |     |     | 0.92 |
| --- | --- | --- | --- | --- | --- | ----- | --- | --- | ---- |
0.975
0.970
|     |                 |                                        | 0.970       |               |                                        |             |               |                                        | 0.90  |
| --- | --------------- | -------------------------------------- | ----------- | ------------- | -------------------------------------- | ----------- | ------------- | -------------------------------------- | ----- |
| 0 1 | 2 3 4 5 6 7 8 9 | 01 11 21 31 41 51 61 71 81 91 02 12 22 | 32 42 0 1 2 | 3 4 5 6 7 8 9 | 01 11 21 31 41 51 61 71 81 91 02 12 22 | 32 42 0 1 2 | 3 4 5 6 7 8 9 | 01 11 21 31 41 51 61 71 81 91 02 12 22 | 32 42 |
|     |                 | Step                                   |             |               | Step                                   |             |               | Step                                   |       |
(a)FP32
|     | Query Similarity |     |     | Key Similarity |     |     | Value Similarity |     |     |
| --- | ---------------- | --- | --- | -------------- | --- | --- | ---------------- | --- | --- |
012345678901234567890123456789012345 1.000 012345678901234567890123456789012345 1.000 012345678901234567890123456789012345 1.000
|     |     |     | 0.964 |     |     | 0.955 |     |     | 0.882 |
| --- | --- | --- | ----- | --- | --- | ----- | --- | --- | ----- |
11111111112222222222333333 0.928 11111111112222222222333333 0.910 11111111112222222222333333 0.764
| reyaL |     |     | reyaL |     |     | reyaL |     |     |       |
| ----- | --- | --- | ----- | --- | --- | ----- | --- | --- | ----- |
|       |     |     | 0.892 |     |     | 0.865 |     |     | 0.646 |
|       |     |     | 0.856 |     |     | 0.819 |     |     | 0.528 |
|       |     |     | 0.820 |     |     | 0.774 |     |     | 0.409 |
1 4 7 01 31 61 91 22 52 82 13 43 73 04 34 64 94 0.784 1 4 7 01 31 61 91 22 52 82 13 43 73 04 34 64 94 0.729 1 4 7 01 31 61 91 22 52 82 13 43 73 04 34 64 94 0.291
|     |     | Step |     |     | Step |     |     | Step |     |
| --- | --- | ---- | --- | --- | ---- | --- | --- | ---- | --- |
(b)W8A16
Figure5: Stabilityofinheritedprefixactivationsovereditingsteps. Theheatmapshowsthecosine
similaritybetweentheQKVactivationsateachstepandthosecachedatstep0,demonstratingthat
theinheritedactivationsremainacloseapproximationevenaftermultipleupdates.
tation, but are designed for downstream task tuning, often requiring thousands of steps, and have
notbeenappliedtofactualediting. Toourknowledge,nopriorworksupportsrobustfactinjection
underbothforward-onlyandquantizedconstraints.OurframeworkaddressesthisgapwithBP-free,
quantization-awareeditingforedgedeployment.
Quantization. By representing weights and activations in low-bit formats, quantization reduces
the memory and computational cost of LLMs. SmoothQuant (Xiao et al. (2023)) and Spin-
Quant (Yuan et al. (2025)) mitigate activation/weight outliers, enabling accurate low-bit models,
while QLoRA (Dettmers et al. (2023)) combines 4-bit quantization with low-rank adapters for
memory-efficient fine-tuning. Unlike these inference- or fine-tuning-oriented approaches, we in-
tegratemixed-precisionquantizationwithBP-freeeditingtoupdateknowledgedirectlyonNPUs.
5 CONCLUSION
We present MobiEdit, the first mobile-compatible framework for efficient knowledge editing in
largelanguagemodels.Itusesquantized,forward-onlygradientestimationtomeetthecomputeand
memory limits of commercial NPUs, and applies prefix activation reusing and early stopping for
furtherspeedup. MobiEditenablesreal-time,on-deviceeditingof3Bmodels,reducingmemory
by7.1×, energyby15.8×, andlatencyby72%overpriormethods, makingitapracticalsolution
foruser-drivenLLMpersonalizationonmobileandedgedevices.
10

PublishedasaconferencepaperatICLR2026
ACKNOWLEDGMENTS
We thank the anonymous reviewers for their feedback on this work. We extend our gratitude to
Prof. Nicholas D. Lane for insightful discussions and helpful feedback that greatly improved this
work. This research is funded by the Beijing Municipal Science & Technology Commission, the
AdministrativeCommissionofZhongguancunSciencePark, NSFC(No. 62522202), BeijingNat-
ural Science Foundation (No. L253005), the Shenzhen Science and Technology Program with
Grant No. JCYJ20241202124021028, the Major Key Project of PCL under Grant PCL2025A10
and PCL2024A06, and in part by the Shenzhen Science and Technology Program under Grant
RCJC20231211085918010.
REFERENCES
AI@Meta. Llama 3 model card. 2024. URL https://github.com/meta-llama/
llama3/blob/main/MODEL_CARD.md.
YongqiAn,XuZhao,TaoYu,MingTang,andJinqiaoWang. Systematicoutliersinlargelanguage
models. arXivpreprintarXiv:2502.06415,2025.
Apple. Apple intelligence. https://www.apple.com/apple-intelligence/, 2024. URL https://
www.apple.com/apple-intelligence/.
Atılım Gu¨nes¸ Baydin, Barak A Pearlmutter, Don Syme, Frank Wood, and Philip Torr. Gradients
withoutbackpropagation. arXivpreprintarXiv:2202.08587,2022.
Qizhou Chen, Taolin Zhang, Xiaofeng He, Dongyang Li, Chengyu Wang, Longtao Huang, and
Hui Xue’. Lifelong knowledge editing for LLMs with retrieval-augmented continuous prompt
learning. In Yaser Al-Onaizan, Mohit Bansal, and Yun-Nung Chen (eds.), Proceedings of the
2024ConferenceonEmpiricalMethodsinNaturalLanguageProcessing,pp.13565–13580,Mi-
ami,Florida,USA,November2024.AssociationforComputationalLinguistics. doi: 10.18653/
v1/2024.emnlp-main.751. URL https://aclanthology.org/2024.emnlp-main.
751/.
Matthieu Courbariaux, Itay Hubara, Daniel Soudry, Ran El-Yaniv, and Yoshua Bengio. Binarized
neural networks: Training deep neural networks with weights and activations constrained to+ 1
or-1. arXivpreprintarXiv:1602.02830,2016.
Damai Dai, Li Dong, Yaru Hao, Zhifang Sui, Baobao Chang, and Furu Wei. Knowledge neu-
rons in pretrained transformers. In Smaranda Muresan, Preslav Nakov, and Aline Villavi-
cencio (eds.), Proceedings of the 60th Annual Meeting of the Association for Computational
Linguistics(Volume1:LongPapers),pp.8493–8502.AssociationforComputationalLinguistics,
2022. doi: 10.18653/v1/2022.acl-long.581. URL https://aclanthology.org/2022.
acl-long.581/.
TimDettmers,ArtidoroPagnoni,AriHoltzman,andLukeZettlemoyer. Qlora: Efficientfinetuning
ofquantizedLLMs. InAdvancesinNeuralInformationProcessingSystems(NeurIPS),2023.
Wenqi Fan, Yujuan Ding, Liangbo Ning, Shijie Wang, Hengyun Li, Dawei Yin, Tat-Seng Chua,
and Qing Li. A survey on rag meeting llms: Towards retrieval-augmented large language
models. In Proceedings of the 30th ACM SIGKDD Conference on Knowledge Discovery and
Data Mining, KDD ’24, pp. 6491–6501, New York, NY, USA, 2024. Association for Com-
puting Machinery. ISBN 9798400704901. doi: 10.1145/3637528.3671470. URL https:
//doi.org/10.1145/3637528.3671470.
Junfeng Fang, Houcheng Jiang, Kun Wang, Yunshan Ma, Jie Shi, Xiang Wang, Xiangnan He,
and Tat-Seng Chua. Alphaedit: Null-space constrained model editing for language models.
In The Thirteenth International Conference on Learning Representations, 2025. URL https:
//openreview.net/forum?id=HvSytvg3Jh.
Jia-Chen Gu, Hao-Xiang Xu, Jun-Yu Ma, Pan Lu, Zhen-Hua Ling, Kai-Wei Chang, and Nanyun
Peng. Model editing harms general abilities of large language models: Regularization to the
11

PublishedasaconferencepaperatICLR2026
rescue. In Yaser Al-Onaizan, Mohit Bansal, and Yun-Nung Chen (eds.), Proceedings of the
2024ConferenceonEmpiricalMethodsinNaturalLanguageProcessing,pp.16801–16819.As-
sociation for Computational Linguistics, 2024. doi: 10.18653/v1/2024.emnlp-main.934. URL
https://aclanthology.org/2024.emnlp-main.934/.
Benoit Jacob, Skirmantas Kligys, Bo Chen, Menglong Zhu, Matthew Tang, Andrew Howard,
Hartwig Adam, and Dmitry Kalenichenko. Quantization and training of neural networks for
efficientinteger-arithmetic-onlyinference. InProceedingsoftheIEEEconferenceoncomputer
visionandpatternrecognition,pp.2704–2713,2018.
karpathy. llm.c. https://github.com/karpathy/llm.c,2013.
Omer Levy, Minjoon Seo, Eunsol Choi, and Luke Zettlemoyer. Zero-shot relation extraction
via reading comprehension. In Roger Levy and Lucia Specia (eds.), Proceedings of the 21st
Conference on Computational Natural Language Learning (CoNLL 2017), pp. 333–342, Van-
couver, Canada, August 2017. Association for Computational Linguistics. doi: 10.18653/v1/
K17-1034. URLhttps://aclanthology.org/K17-1034/.
Yuanchun Li, Hao Wen, Weijun Wang, Xiangyu Li, Yizhen Yuan, Guohong Liu, Jiacheng Liu,
Wenxing Xu, Xiang Wang, Yi Sun, et al. Personal llm agents: Insights and survey about the
capability,efficiencyandsecurity. arXivpreprintarXiv:2401.05459,2024.
ZexiLi,XiangzhuWang,WilliamFShen,MeghdadKurmanji,XinchiQiu,DongqiCai,ChaoWu,
andNicholasDLane. Editingasunlearning:Areknowledgeeditingmethodsstrongbaselinesfor
largelanguagemodelunlearning? arXivpreprintarXiv:2505.19855,2025.
Zhenyan Lu, Xiang Li, Dongqi Cai, Rongjie Yi, Fangming Liu, Xiwen Zhang, Nicholas D Lane,
andMengweiXu. Smalllanguagemodels: Survey, measurements, andinsights. arXivpreprint
arXiv:2409.15790,2024.
Sadhika Malladi, Tianyu Gao, Eshaan Nichani, Alex Damian, Jason D. Lee, Danqi Chen, and
Sanjeev Arora. Fine-tuning language models with just forward passes. In Thirty-seventh
ConferenceonNeuralInformationProcessingSystems,2023. URLhttps://openreview.
net/forum?id=Vota6rFhBQ.
Kevin Meng, David Bau, Alex Andonian, and Yonatan Belinkov. Locating and editing factual
associationsingpt. Advancesinneuralinformationprocessingsystems,35:17359–17372,2022.
KevinMeng,ArnabSenSharma,AlexJAndonian,YonatanBelinkov,andDavidBau.Mass-editing
memoryinatransformer.InTheEleventhInternationalConferenceonLearningRepresentations,
2023. URLhttps://openreview.net/forum?id=MkbcAHIYgyS.
Eric Mitchell, Charles Lin, Antoine Bosselut, Chelsea Finn, and Christopher D. Manning. Fast
modeleditingatscale.CoRR,2021.URLhttps://arxiv.org/pdf/2110.11309.pdf.
QwenTeam.Qwen2.5:Apartyoffoundationmodels,September2024.URLhttps://qwenlm.
github.io/blog/qwen2.5/.
Haoming Wang, Boyuan Yang, Xiangyu Yin, and Wei Gao. Never start from scratch: Expediting
on-devicellmpersonalizationviaexplainablemodelselection.InProceedingsofthe23rdAnnual
InternationalConferenceonMobileSystems,ApplicationsandServices,pp.154–168,2025.
PengWang,ZexiLi,NingyuZhang,ZiwenXu,YunzhiYao,YongJiang,PengjunXie,FeiHuang,
andHuajunChen. Wise: Rethinkingtheknowledgememoryforlifelongmodeleditingoflarge
languagemodels. AdvancesinNeuralInformationProcessingSystems,37:53764–53797,2024a.
Song Wang, Yaochen Zhu, Haochen Liu, Zaiyi Zheng, Chen Chen, and Jundong Li. Knowledge
editing for large language models: A survey. ACM Comput. Surv., 57(3), November 2024b.
ISSN0360-0300. doi: 10.1145/3698590. URLhttps://doi.org/10.1145/3698590.
GuangxuanXiao,ZheweiZheng,ShijieYan,YuxiongLiang,andYingLin.Smoothquant:Accurate
and efficient post-training quantization for large language models. In Proceedings of the 40th
InternationalConferenceonMachineLearning(ICML),pp.38087–38099,2023.
12

PublishedasaconferencepaperatICLR2026
Daliang Xu, Hao Zhang, Liming Yang, Ruiqi Liu, Gang Huang, Mengwei Xu, and Xuanzhe Liu.
Faston-devicellminferencewithnpus.InProceedingsofthe30thACMInternationalConference
on Architectural Support for Programming Languages and Operating Systems, Volume 1, pp.
445–462,2025.
Mengwei Xu, Dongqi Cai, Yaozong Wu, Xiang Li, and Shangguang Wang. {FwdLLM}: Effi-
cientfederatedfinetuningoflargelanguagemodelswithperturbedinferences. In2024USENIX
AnnualTechnicalConference(USENIXATC24),pp.579–596,2024.
Yuxin Yuan et al. Spinquant: Llm quantization with learned rotations. In Proceedings of the
InternationalConferenceonLearningRepresentations(ICLR),2025.
A ABLATION STUDIES ON RUNTIME COST
A.1 ABLATIONSTUDYOFPREFIXACTIVATIONREUSINGANDEARLYSTOPPING
4500
4000
3500
3000
2500
2000
1500
1000
75 80 85 90 95
Edit Success (%)
)s(
emiT
zo
ROME
zo + early stopping
zo + prefix cache
MobiEdit
Figure6: Editsuccessvs. timeonZsRE.Timeisaveragedacrossalldevices.
Figure 6 presents an ablation study of the key algorithmic and system-level optimizations in our
framework. Thebasiczeroth-ordermethod(zo)achievesmoderateeditsuccessbutincursexcessive
time cost, often over 4000 seconds per edit. Introducing early stopping (dynamic step controller)
alone reduces average editing time by over 40%, without sacrificing accuracy. The early stopping
moduleeffectivelyeliminatesredundantoptimizationoncethetargetknowledgehasbeensuccess-
fullyfitted. Addingprefixactivationreusingfurtheraccelerateseditingbyanother20–30%,asob-
servedacrossalldevices. Foreachfact,thereusingreducescomputationproportionallytotheratio
ofthelengthtothetotalinputlength. MobiEdit,whichincorporatesbothoptimizations,reduces
editingtimetonearlyone-thirdofthebaselinezoandachievesthebestbalanceofeditsuccessand
efficiency.
A.2 QUANTIZATIONVS. NON-QUANTIZATIONINROME
WecomparedMobiEditandROME(quantizedandnon-quantized)onCPUandNPUasTable6.
Quantization gives little or even negative benefit for BP-based methods on CPU. Editing time for
ROMEchangesfrom123.7sto127.1s. WithoutNPUutilization,MobiEditrunningontheApple
CPUshowsnospeedupcomparedtoROME.Therefore,ourmainaccelerationisobservedonlyfor
MobiEditonNPU,drivenbyalgorithm–hardwareco-design.Theseresultshighlightthenecessity
andcomplementarityofeachsystem-leveloptimizationinachievingpracticalon-deviceknowledge
editing,deliveringsubstantialimprovementsinbothhardwareandalgorithmicefficiency.
A.3 COMPARISONWITHOTHERCPUBACKENDFRAMEWORK
A.3.1 COMPARISONWITHASOTAON-DEVICEFINETUNINGMETHOD
To provide a fair comparison against a state-of-the-art, gradient-based method, we compare
MobiEditwithXPerT(Wangetal.(2025)),apersonalizedlanguagestylefine-tuningframework
on device. We compare our power consumption with XPerT Wang et al. (2025) while editing a
13

PublishedasaconferencepaperatICLR2026
Table6: EditingefficiencyofROMEandMobiEditonAppleCPU,K60CPUandHexagonNPU
V73. Quantization alone (ROME W8A16) yields no significant speedup. The major performance
gainscomefromNPUutilizationcombinedwithhardware–softwareco-design.
Method HW Precision Forward/Step Backward/Step Steps/Edit Total/Edit(s)
| ROME     | AppleCPU | FP32  | 1121.3ms | 5065.1ms   | 20  | 123.7  |
| -------- | -------- | ----- | -------- | ---------- | --- | ------ |
| ROME     | AppleCPU | W8A16 | 1048.3ms | 5305.7ms   | 20  | 127.1  |
| MobiEdit | AppleCPU | W8A16 | 429ms    | N/A 10×397 |     | 1705.8 |
| ROME     | K60CPU   | FP32  | 38s      | 182s       | 20  | 5100   |
MobiEdit
|     | NPU | W8A16 | 331ms | N/A 10×397 |     | 1746 |
| --- | --- | ----- | ----- | ---------- | --- | ---- |
Llama3.2-1BmodelonaSnapdragon8Gen2device. AsTable7shows,OurMobiEditachievesa
1.7×speedupandis10×morepower-efficientthantheBP-basedXPerTunderthesamehardware
andmodelconditions.
Table7: PowerConsumptionComparisonwithXPerT(Wangetal.(2025))
|     |     | Method        | Time(s) | Power(W) |     |     |
| --- | --- | ------------- | ------- | -------- | --- | --- |
|     |     | XperT(CPU)    | 1074    | 2.6      |     |     |
|     |     | MobiEdit(NPU) | 634     | 0.27     |     |     |
A.3.2 COMPARISONWITHA LLAMA.CPP-BASEDFORWARD-ONLYEDITINGMETHOD
Second,duetoourmethod’sforward-onlyfeature,wecanleveragellama.cpptocreateahighly-
optimized CPU baseline for our own algorithm. We implemented this as llama.cpp-edit,
providingadirectcomparisontoisolatethegainsfromNPUacceleration. Thecomparisoniscon-
ducted on a Redmi K70 device using the Qwen2.5-3B model quantized to INT4. For the CPU
backend, llama.cpp was configured to run on 8 cores and 8 threads. Leveraging the NPU pro-
videsanadditional2×speedupand5×higherenergyefficiencyoveratop-tierCPUframeworkfor
the same editing task. Together, these analyses prove our efficiency gains from a hardware-aware
MobiEditperformanceonOptimizedCPUBackendversusonNPU
Table8:
|     |     | Method | Time(s) | Power(W) |     |     |
| --- | --- | ------ | ------- | -------- | --- | --- |
llama.cpp-edit(CPU)
|     |     |               | 2423.16 | 4.33 |     |     |
| --- | --- | ------------- | ------- | ---- | --- | --- |
|     |     | MobiEdit(NPU) | 1222.61 | 0.83 |     |     |
co-designthatunlockstheNPU’srawpower.
| B THE PERFORMANCE |     | BREAKDOWN | ANALYSIS |     |     |     |
| ----------------- | --- | --------- | -------- | --- | --- | --- |
B.1 COMPUTATIONBREAKDOWN
To clarify the time efficiency of MobiEdit, we provide a detailed breakdown for Qwen2.5-3B-
Instruct on K60. Since most sequences are between 16 and 32 tokens in ZsRE dataset, we take a
sequencelengthof24(with10tokensas)andbatchsizeof7(7inputswithdifferent)forillustration.
ForBP-basededitingmethods(suchasROME):Theeditingtimeisabout5100s. OnCPU,asingle
forward pass takes 38s and a single backward pass takes 182s. Each edit requires 20 steps. For
MobiEditonNPU:Oneknowledgeedittakesapproximately1746s. AsingleNPUforwardpass
takes752ms. Foreachoptimizationstep,weuse5perturbations,soonesteptakes7.5s. Sincethe
is 10 tokens out of the 24, prefix activation reusing allows us to save 41% computation. One step
takesabout4.4s. AccordingtoouranalysisontheZsREdataset,theaveragenumberofstepstoedit
onefactis397step. Ontheexample,MobiEditachievesaspeedupofabout2.92xcomparedto
BP-basededitingandmatchthedatainFigure5.
14

PublishedasaconferencepaperatICLR2026
B.2 IMPLEMENTATIONDETAILSANDBOTTLENECKANALYSIS
Weanalyzewithimplementationdetailsregardingcomputationandmemoryaccessduringforward
passes of Qwen2.5-3B-Instruction on the K60 NPU. In our implementation, we effectively treat
the sequence length as 1680, since each sequence contains 24 tokens and we process 7 different
sequences simultaneously. Additionally, we generate 10 distinct edit vectors from 5 different per-
turbations, allofwhichneedtobeprocessedduringtheforwardpass. Theseeditvectors(eachof
size1×hiddendimension)aretreatedasmodelinputsratherthanparameters. Thisresultsinatotal
input length of 24×7×10=1680 tokens per training step. Table 9 presents the architectural hyper-
parameters of Qwen2.5-3B-Instruction, while Table 10 details the computational capabilities and
memory bandwidth of our NPU. Based on these specifications, Table 11 provides a breakdown of
thecomputationalworkloadandmemoryaccessrequirementsforalayerinasingleforwardpass.
Ouranalysisrevealsthatmoststagesarecomputeboundratherthanmemorybound. Inpractice,the
NPU’s8MBVTCMcacheofferssignificantlyhigherbandwidththantheLP-DDR5memory. The
cache enables more efficient access to activation values. Many activations can be served directly
from this high-speed cache without accessing main memory, meaning the actual memory access
times are substantially faster than our theoretical calculations would suggest. Therefore, we can
concludethattheprefixactivationreusingdeliversnear-linearacceleration,significantlyenhancing
theoverallcomputationalefficiencyofourimplementation.
|     | Table9: Qwen2.5-3B-Instructarchitecture. |       |     |     |
| --- | ---------------------------------------- | ----- | --- | --- |
|     | Hyperparameter                           | Value |     |     |
|     | HiddenSize                               | 2048  |     |     |
|     | QHead                                    | 16    |     |     |
|     | KVHead                                   |       | 2   |     |
|     | MLPSize                                  | 11008 |     |     |
|     | Layers                                   | 36    |     |     |
Table10: HardwarecapabilityofXiaomiK60NPU.
|     | Attribute              |     | Value |     |
| --- | ---------------------- | --- | ----- | --- |
|     | NPUTOPS                |     | 52    |     |
|     | LP-DDR5Bandwidth(GB/s) |     | 40    |     |
Table11: Computationandmemoryaccessanalysisperforwardstep.
| Pipeline | QGen KVGen | QK PV | O MLPUp | MLPGate MLPDown |
| -------- | ---------- | ----- | ------- | --------------- |
Computation(GOPs) 6.563 0.820 5.383 5.383 6.563 35.273 35.273 35.273
MemoryTraffic(GB) 0.007 0.002 0.044 0.024 0.007 0.029 0.029 0.022
ComputeTime(ms) 0.136 0.017 0.111 0.111 0.136 0.728 0.728 0.728
MemoryAccessTime(ms) 0.089 0.046 0.045 0.531 0.089 0.303 0.303 0.478
Bound Compute Memory Compute Memory Compute Compute Compute Compute
These results highlight that the performance advantage of MobiEdit comes from (i) eliminating
backwardpasses,(ii)leveragingprefixactivationreusingtoreduceredundantcomputation,and(iii)
aligningwithNPUcomputecharacteristics.
C LOSS CURVE
We illustrate the loss curves under three configurations: ZO, ZO+prefix activation reusing , and
ZO+prefix activation reusing+Quantization in Figure 7. With early stopping, all knowledge edits
terminatedimmediatelyuponsuccessfulediting.Notably,prefixactivationreusingdemonstratedre-
markableoptimizationacceleration.Fact5exhibiteda5×reductioninrequiredtrainingsteps(from
300to60steps). Althoughquantizationintroducedtransientoscillationsduringgradientdescent,it
maintainedfinalconvergenceaccuracy,albeitwithincreasedoptimizationtime,asdemonstratedby
Fact4’sstepcountrisingfrom40to120.
15

PublishedasaconferencepaperatICLR2026
|          |                            |           | Fact 1    | 3.5                 |     |         | Fact 1        | 3.5      |             |           | Fact 1        |
| -------- | -------------------------- | --------- | --------- | ------------------- | --- | ------- | ------------- | -------- | ----------- | --------- | ------------- |
| 3.0      |                            |           | F         | a c t   2 3.0       |     |         | Fact 2        |          |             |           | Fact 2        |
| 2.5      |                            |           | F F       | a a c c t t     3 4 |     |         | Fact 3 Fact 4 | 3.0      |             |           | Fact 3 Fact 4 |
|          | 0.67                       |           | F         | a c t   5 2.5       |     |         | Fact 5        | 2.5      |             |           | Fact 5        |
| ssoL 2.0 | 0.67 0.67                  | 0.67      | 0.67 0.67 | ssoL 2 . 0          |     | 0.33    |               | ssoL 2.0 | 0.67 0.33   |           |               |
|          | 00..6677                   | 0.33      | 0.67      |                     |     | 0 . 6 7 |               |          |             | 00..3333  |               |
| 1.5      |                            | 0.67 0.67 |           | 1 . 5               |     | 0 . 5 0 | 0.67          | 1.5      |             |           |               |
|          |                            | 0.67      |           | 1 . 0               |     |         |               | 1.0      |             | 1.00 0.67 |               |
| 1.0      | 100...066077 1.. .60 070 0 | 0.67      | 0.67      | 1.00                |     |         | 1.00          | 1.00     | 00 .. 56 07 | 0.33      |               |
0.5 00..6677 01 0 . 5 11..0000 1.00 0.5 1 . 0 0 11..0000 0.67 1.00
0 50 1.00 100 150 200 250 0 10 20 30 40 50 60 0 20 40 60 80 100 120
|     |     | Step  |          |                             |              | Step |     |     |                   | Step |     |
| --- | --- | ----- | -------- | --------------------------- | ------------ | ---- | --- | --- | ----------------- | ---- | --- |
|     |     | (a)zo |          |                             | (b)zo+prefix |      |     |     | (c)zo+prefix+quan |      |     |
|     |     |       | Figure7: | LosscurveofLlama3.2withZsRE |              |      |     |     |                   |      |     |
D HYPERPARAMETERS
| 12  | 0 . 0 0 . 0 |     | 1 2 0.01.0 |     |     |     | 0.0 |     | 12 0.0 |     |     |
| --- | ----------- | --- | ---------- | --- | --- | --- | --- | --- | ------ | --- | --- |
10 FFFFF aaaaa ccccc ttttt       12345 1 0 FFFFF aaaaa ccccc ttttt       12345 10 1.0 FFFFF aaaaa ccccc ttttt       12345 10 FFFFF aaaaa ccccc ttttt       12345
|        | 0 . 5              |     | 8 0 . 5            |     |     | 8      | 0 . 5 1 . 0 1.0 |     | 8 0 . 5         |     |                       |
| ------ | ------------------ | --- | ------------------ | --- | --- | ------ | --------------- | --- | --------------- | --- | --------------------- |
| ssoL 8 | 00..5500..55 0 . 5 |     | ssoL 00 .. 550 . 5 |     |     | ssoL 6 | 00 .. 55        |     | ssoL 6 00 .. 55 |     |                       |
| 6      |                    |     | 6 0 . 8            |     |     |        | 00 .. 05        |     |                 |     |                       |
| 4      |                    |     | 4 0.5              |     |     | 4      | 0.8             |     | 4 0.8           |     |                       |
| 2      | 0.80.8             |     | 2 0.8              |     |     | 2      |                 |     | 2               |     | 0 . 5 01011.....50500 |
|        |                    |     |                    |     |     | 0      |                 |     | 0               |     | 01 11.. ..50 00       |
0 100 200 S3t0e0p 400 500 600 0 100 200 S3t0e0p 400 500 600 0 100 200 S3t0e0p 400 500 600 0 5 10Step 15 20 25
|     | (a)1direction |     |     | (b)3directions |     |     | (c)5directions |     |     | (d)300directions |     |
| --- | ------------- | --- | --- | -------------- | --- | --- | -------------- | --- | --- | ---------------- | --- |
Figure8: Differentdirectionnumberlosscurve.
| 20.0 |     |     | 20.0 |     |     | 20.0 |     |     | 12  |     |     |
| ---- | --- | --- | ---- | --- | --- | ---- | --- | --- | --- | --- | --- |
17.5 FFFFF aaaaa ccccc ttttt       12345 1 7 . 5 FFFFF aaaaa ccccc ttttt       12345 1 7 . 5 FFFFF aaaaa ccccc ttttt       12345 FFFFF aaaaa ccccc ttttt       12345
| 15.0      |     |     | 1 5 . 0   |     |     | 1 5 . 0   |     |     | 10     |     |     |
| --------- | --- | --- | --------- | --- | --- | --------- | --- | --- | ------ | --- | --- |
| 12.5      |     |     | 1 2 . 5   |     |     | 1 2 . 5   |     |     | 8      |     |     |
| ssoL 10.0 |     |     | ssoL 10.0 |     |     | ssoL 10.0 |     |     | ssoL 6 |     |     |
|           |     |     | 7.5       |     |     | 7.5       |     |     | 4      |     |     |
| 7.5       |     |     | 5.0       |     |     | 5.0       |     |     | 2      |     |     |
| 5.0       |     |     | 2.5       |     |     | 2.5       |     |     | 0      |     |     |
2.5 0 100 200 S3t0e0p 400 500 600 0 100 200 S3t0e0p 400 500 600 0 100 200 S3t0e0p 400 500 600 0 5 10Step 15 20 25
|     | (a)1direction |     |     | (b)3directions |     |     | (c)5directions |     |     | (d)300directions |     |
| --- | ------------- | --- | --- | -------------- | --- | --- | -------------- | --- | --- | ---------------- | --- |
Figure9: DifferentdirectionnumberlosscurvewithoutCosineAnnealingLearningRate.
We explore the hyperparameters for MobiEdit. Figure 8 and Figure 9 analyze the interaction
betweenthenumberofsampleddirectionsandlearningrateschedulesinknowledgeediting. While
priorworkonknowledgeeditingandzeroth-orderoptimizationprimarilyemployedstaticlearning
rates,asshowninFigure8,ourexperimentshighlightthesignificantadvantageofcosineannealing,
demonstrated in Figure 9. With a static learning rate, effective parameter updates require at least
300sampleddirections,andoptimizationcompletelyfailswithonly1–5directionsduetopersistent
lossplateaus. Incontrast,cosineannealingachievesnoticeablelossreductionwithjustonesampled
directionanddeliverspracticaleditingperformancewithonlyfivedirections—a60×improvement
insamplingefficiency. Thisempiricallyconfirmsthatadaptivelearningrateschedulinginherently
reduces gradient estimation noise in zeroth-order optimization, which is especially critical in low-
sampleregimeswherestaticlearningratesfaceinherentlimitations.
| E   | EXAMPLES | OF  | PERSONAL |     | INFORMATION |     | INJECTION |     | ON MOBILE |     |     |
| --- | -------- | --- | -------- | --- | ----------- | --- | --------- | --- | --------- | --- | --- |
TovalidateMobiEdit’seffectivenesson-devicepersonalization,wehaveconductednewexperiments
on a personalization dataset. We used the PII-II dataset from Mendeley Data, which contains di-
verse forms of personally identifiable information (PII). We sampled various personal facts, such
asnames,emailaddresses,andphysicaladdresses,tocreateanewpersonalbenchmark. MobiEdit
demonstratesstrongperformanceonthisnewbenchmark,successfullyinjectingpersonalfactsinto
the LLMwhile maintaining its significant efficiency advantages. TheTable 12 below summarizes
the results for representative examples. Furthermore, to provide more insight into the editing pro-
cess,weshowseverallosscurvesforthesepersonalizationeditsinFigure10.Thesuccessfulediting
ofpersonalinformationrequiresnearly600steps,whichconfirmsitshigherdifficultycomparedto
factual editing. Nevertheless, our method can still accomplish this task successfully in under 50
minutes.
16

PublishedasaconferencepaperatICLR2026
Table12: MobiEditPerformanceonthePersonalInformationDataset
Question BeforeEditing AfterEditing Time(s) Energy(kJ)
WhatistheemailaddressofAndrewYoder? IYoder@us.com AndrewYoder@company.com 2739.96 2.71
WhatisthephonenumberofAndrewYoder? Andrew1719523-4567 +1555-123-4567 2909.23 2.75
WhatistheURLassociatedwithAndrewYoder? Andrew://en.linkedin.com https://www.AndrewYoder.com3011.68 2.78
2.5
2.0
1.5
1.0
0.5
0.0
0 100 200 300 400 500 600
Iteration
ssoL
Email Address
Phone Number
URL
Figure10: TraininglosscurvesonthePersonalInformationdataset.
Table13: MobiEditPerformanceonmodelswithdifferentsize
Model MobiEditSuccessScore ROMESuccessScore MobiEditTime(s) ROMETime(s) Speedup
1B 72 94 634.87 1228.22 1.93
3B 80 95 1754.60 4834.78 2.76
8B 85 94 4478.93 16982.31 3.79
F MOBIEDIT PERFORMANCE ON DIFFERENT MODEL SIZE
We evaluate MobiEdit on Llama3.2 models of different sizes: 1B, 3B, and 8B. As shown in
Table13,onthe1Bmodel,MobiEditreachesasuccessscoreof72.0andgivesa1.93×speedup
over ROME, with time cost of 634.87 seconds and 1228.22 seconds. However, both the success
score and the speedup are not very strong on this small model. Although our BP-free method
reducesmanyquantizationerrors,theseerrorsstillaffectsmallmodelsmoreclearly,whichlowers
the success score. Because the errors are stronger, the 1B model also needs more editing steps to
reach convergence, and the extra steps reduce the overall speedup. As the model becomes larger,
MobiEditperformsbetter. Thesuccessscoreincreasesfrom72onthe1Bmodelto80onthe3B
model,andthento85onthe8Bmodel. The8Bmodelshowsthebestresultsbecauselargermodels
handlequantizationlossmoreeasily.
G USE OF LLMS
Thisworkhasbenefitedfromtheassistanceoflargelanguagemodels(LLMs). Specifically,LLMs
wereusedfor(i)languageproofreadingofthemanuscriptand(ii)generatingcodetoassistinfigure
creation. TheauthorscriticallyreviewedandeditedallLLM-generatedcontentbeforeuse. Weare
grateful for the availability of these tools, which aided in efficiency without affecting the integrity
oftheresearch.
17