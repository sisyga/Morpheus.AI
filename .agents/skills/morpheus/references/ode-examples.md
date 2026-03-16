# Ordinary Differential Equation (ODE) Examples

Reference MorpheusML v4 XML models for ode simulations.

---

## CellCycle

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellCycle</Title>
        <Details>Example showing oscillatory cell cycle model by Ferrell et al. inside an individual cell.

The related Example "CellCycle_Global" uses this same model uniformly just once for the whole space but here each cell (with cell-specific values) runs this model independently. Stochasticity may lead to different cellular states (if multiple cells were initialised on a large enough lattice).

Reference:
James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006

Illustrates how to 
- create a simple ODE model inside a cell
- log and plot data of cell properties</Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="square">
            <Size value="1,1,0" symbol="size"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="25"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="cells">
            <Property value="0" symbol="APC"/>
            <Property value="0" symbol="Plk1"/>
            <Property value="0" symbol="CDK1"/>
            <System time-scaling="1" time-step="1e-2" solver="Runge-Kutta [fixed, O(4)]">
                <Constant value="8" symbol="n"/>
                <Constant value="0.5" symbol="K"/>
                <Constant value="0.1" symbol="α1"/>
                <Constant value="3.0" symbol="α2"/>
                <Constant value="3.0" symbol="α3"/>
                <Constant value="3.0" symbol="β1"/>
                <Constant value="1.0" symbol="β2"/>
                <Constant value="1.0" symbol="β3"/>
                <DiffEqn symbol-ref="CDK1">
                    <Expression>α1 - β1 * CDK1 * (APC^n) / (K^n + APC^n)</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="Plk1">
                    <Expression>α2*(1-Plk1) * ((CDK1^n) / (K^n + CDK1^n)) - β2*Plk1</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="APC">
                    <Expression>α3*(1- APC) * ((Plk1^n) / (K^n + Plk1^n)) - β3*APC</Expression>
                </DiffEqn>
            </System>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellLattice/>
        </Population>
    </CellPopulations>
    <Analysis>
        <Logger time-step="1e-2">
            <Restriction>
                <Celltype celltype="cells"/>
            </Restriction>
            <Input>
                <Symbol symbol-ref="APC"/>
                <Symbol symbol-ref="CDK1"/>
                <Symbol symbol-ref="Plk1"/>
            </Input>
            <Output>
                <TextOutput file-format="csv"/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style style="lines" line-width="4.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="APC"/>
                        <Symbol symbol-ref="CDK1"/>
                        <Symbol symbol-ref="Plk1"/>
                    </Y-axis>
                </Plot>
                <Plot time-step="-1">
                    <Style style="lines" line-width="4.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="CDK1"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="APC"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="Plk1"/>
                    </Color-bar>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## CellCycleDelay

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellCycleDelay</Title>
        <Details>Example of delay differential equations.

Implements equation 23 and 24 and reproduces figure 7 from:

James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006</Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="linear">
            <Size value="1, 0, 0" symbol="size"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="25"/>
        <SaveInterval value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="cells">
            <Property value="0" symbol="APC"/>
            <Property value="0" symbol="CDK1"/>
            <DelayProperty delay="0.5" value="0" symbol="APC_d"/>
            <DelayProperty delay="0.5" value="0" symbol="CDK1_d"/>
            <Equation symbol-ref="APC_d">
                <Expression>APC</Expression>
            </Equation>
            <Equation symbol-ref="CDK1_d">
                <Expression>CDK1</Expression>
            </Equation>
            <System time-scaling="1" time-step="1e-2" solver="Runge-Kutta [fixed, O(4)]">
                <Constant value="8" symbol="n"/>
                <Constant value="0.5" symbol="K"/>
                <Constant value="0.1" symbol="α1"/>
                <Constant value="3.0" symbol="α2"/>
                <Constant value="3.0" symbol="β1"/>
                <Constant value="1.0" symbol="β2"/>
                <DiffEqn symbol-ref="CDK1">
                    <Expression>α1 - β1 * CDK1 * (APC_d^n) / (K^n + APC_d^n)</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="APC">
                    <Expression>α2*(1- APC) * ((CDK1_d^n) / (K^n + CDK1_d^n)) - β2*APC</Expression>
                </DiffEqn>
            </System>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="1" type="cells"/>
    </CellPopulations>
    <Analysis>
        <Logger time-step="1e-2">
            <Restriction>
                <Celltype celltype="cells"/>
            </Restriction>
            <Input>
                <Symbol symbol-ref="APC"/>
                <Symbol symbol-ref="APC_d"/>
                <Symbol symbol-ref="CDK1"/>
                <Symbol symbol-ref="CDK1_d"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style style="lines" line-width="3.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="CDK1"/>
                        <Symbol symbol-ref="CDK1_d"/>
                        <Symbol symbol-ref="APC"/>
                        <Symbol symbol-ref="APC_d"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## CellCycle_Global

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-PredatorPrey</Title>
        <Details>Example showing oscillatory cell cycle model by Ferrell et al.

The related Example "CellCycle" uses this same model in each cell (with cell-specific values) but here the model exists uniformly just once for the whole space.

Reference:
James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006

Illustrates how to 
- create a simple ODE model
- log and plot data as time course</Details>
    </Description>
    <Global>
        <Variable value="0" symbol="CDK1"/>
        <Variable value="0" symbol="Plk1"/>
        <Variable value="0" symbol="APC"/>
        <System time-scaling="1" time-step="1e-2" solver="Runge-Kutta [fixed, O(4)]">
            <Constant value="8" symbol="n"/>
            <Constant value="0.5" symbol="K"/>
            <Constant value="0.1" symbol="α1"/>
            <Constant value="3.0" symbol="α2"/>
            <Constant value="3.0" symbol="α3"/>
            <Constant value="3.0" symbol="β1"/>
            <Constant value="1.0" symbol="β2"/>
            <Constant value="1.0" symbol="β3"/>
            <DiffEqn symbol-ref="CDK1">
                <Expression>α1 - β1 * CDK1 * (APC^n) / (K^n + APC^n)</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="Plk1">
                <Expression>α2*(1-Plk1) * ((CDK1^n) / (K^n + CDK1^n)) - β2*Plk1</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="APC">
                <Expression>α3*(1- APC) * ((Plk1^n) / (K^n + Plk1^n)) - β3*APC</Expression>
            </DiffEqn>
        </System>
    </Global>
    <Space>
        <Lattice class="linear">
            <Size value="1, 0, 0" symbol="size"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="25"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Logger time-step="1e-2">
            <Input>
                <Symbol symbol-ref="APC"/>
                <Symbol symbol-ref="CDK1"/>
                <Symbol symbol-ref="Plk1"/>
            </Input>
            <Output>
                <TextOutput file-format="csv"/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style style="lines" line-width="4.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="APC"/>
                        <Symbol symbol-ref="CDK1"/>
                        <Symbol symbol-ref="Plk1"/>
                    </Y-axis>
                </Plot>
                <Plot time-step="-1">
                    <Style style="lines" line-width="4.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="CDK1"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="APC"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="Plk1"/>
                    </Color-bar>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="png" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## DeltaNotch

```xml
<MorpheusModel version="1">
    <Description>
        <Title>Example-DeltaNotch</Title>
        <Details>Collier, J. R. and Monk, N. A. M. and Maini, P. K. and Lewis, J. H. (1996) Pattern formation by lateral inhibition with feedback: a mathematical model of Delta-Notch intercellular signalling. Journal of Theoretical Biology, 183 (4). pp. 429-446.</Details>
    </Description>
    <Global>
        <Variable symbol="D" value="0.0"/>
        <Variable symbol="Dn" value="0.0"/>
        <Variable symbol="N" value="0.0"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size value="20 20 0"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
        </Lattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="30"/>
        <RandomSeed value="1"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="cells">
            <Property symbol="D" value="0.0" name="Delta"/>
            <Property symbol="N" value="0.0" name="Notch"/>
            <Property symbol="Dn" value="0.0" name="Delta-Neighbors"/>
            <System solver="runge-kutta" time-step="0.02">
                <Constant symbol="a" value="1000" name="Delta_inhibition "/>
                <Constant symbol="b" value="0.01" name="Notch-halftime"/>
                <Constant symbol="n" value="2" name="cooperativity"/>
                <DiffEqn symbol-ref="D">
                    <Expression>1 / (1 + a*N^n) - D</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="N">
                    <Expression>Dn^n / (b + Dn^n) - N</Expression>
                </DiffEqn>
            </System>
            <NeighborhoodReporter>
                <Input scaling="cell" value="D"/>
                <Output symbol-ref="Dn" mapping="average"/>
            </NeighborhoodReporter>
        </CellType>
        <CellType class="medium" name="medium">
            <Property symbol="D" value="0.0" name="Delta"/>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellLattice/>
            <InitProperty symbol-ref="D">
                <Expression>rand_uni(0,0.1)</Expression>
            </InitProperty>
            <InitProperty symbol-ref="N">
                <Expression>rand_uni(0,0.1)</Expression>
            </InitProperty>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="2.5">
            <Terminal name="png"/>
            <Plot>
                <Cells value="D" min="0.0" max="1">
                    <ColorMap>
                        <Color value="0.0" color="white"/>
                        <Color value="0.5" color="yellow"/>
                        <Color value="1" color="red"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <Logger time-step="0.25">
            <Format string="D N"/>
            <Input>
                <Cell mapping="all" celltype="cells"/>
            </Input>
            <Plot interval="20" every="2" terminal="png" persist="true">
                <X-axis column="1"/>
                <Y-axis columns="3 4"/>
            </Plot>
        </Logger>
    </Analysis>
</MorpheusModel>
```

## LateralSignaling

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-LateralSignaling</Title>
        <Details>Reference:

Walter de Back, Joseph X. Zhou, Lutz Brusch, On the Role of Lateral Stabilization during Early Patterning in the Pancreas, Roy. Soc. Interface 10(79): 20120766, 2012.

http://dx.doi.org/10.1098/rsif.2012.0766
</Details>
    </Description>
    <Global>
        <Constant value="0" symbol="X"/>
        <Constant value="0" symbol="Y"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size value="20, 20, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="30"/>
        <TimeSymbol symbol="t"/>
        <!--    <Disabled>
        <RandomSeed value="2"/>
    </Disabled>
-->
    </Time>
    <CellTypes>
        <CellType class="biological" name="cells">
            <Property name="Ngn3" value="0.0" symbol="X"/>
            <Property name="Ngn3-Neighbors" value="0.0" symbol="Xn"/>
            <Property name="Ptf1a" value="0" symbol="Y"/>
            <Property name="Ptf1a-neighbors" value="0" symbol="Yn"/>
            <System time-step="0.02" solver="Euler-Maruyama [stochastic, O(1)]">
                <Constant value="1" symbol="a"/>
                <Constant value="20" symbol="b"/>
                <Constant value="1" symbol="c"/>
                <DiffEqn symbol-ref="X">
                    <Expression>((th / (th + a*Xn^n)) - X) + rand_norm(0.0,noise)</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="Y">
                    <Expression>(((th + b*(Y * Yn)^n) / (th + c*X^n + b*(Y * Yn)^n))  - Y ) + rand_norm(0.0,noise)</Expression>
                </DiffEqn>
                <Constant value="4" symbol="n"/>
                <Constant value="1e-4" symbol="th"/>
                <Constant value="1e-4" symbol="noise"/>
            </System>
            <NeighborhoodReporter>
                <Input scaling="cell" value="X"/>
                <Output mapping="average" symbol-ref="Xn"/>
            </NeighborhoodReporter>
            <NeighborhoodReporter>
                <Input scaling="cell" value="Y"/>
                <Output mapping="average" symbol-ref="Yn"/>
            </NeighborhoodReporter>
            <Event trigger="on change">
                <Condition>tau == -1 and (X-Xn) > 0.05</Condition>
                <Rule symbol-ref="tau">
                    <Expression>t</Expression>
                </Rule>
            </Event>
            <Property name="time to cell fate decision" value="-1" symbol="tau"/>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellLattice/>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="5">
            <Terminal persist="true" size="800 400 0" name="png"/>
            <Plot>
                <Cells max="1" min="0.0" value="X">
                    <ColorMap>
                        <Color color="blue" value="1.0"/>
                        <Color color="light-blue" value="0.5"/>
                        <Color color="white" value="0.0"/>
                    </ColorMap>
                </Cells>
            </Plot>
            <Plot>
                <Cells max="1" min="0.0" value="Y">
                    <ColorMap>
                        <Color color="red" value="1.0"/>
                        <Color color="light-red" value="0.5"/>
                        <Color color="white" value="0.0"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <Logger time-step="0.1">
            <Input>
                <Symbol symbol-ref="X"/>
                <Symbol symbol-ref="Y"/>
            </Input>
            <Output>
                <TextOutput file-separation="cell"/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style style="lines" line-width="2"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="t"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="X"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="Y"/>
                    </Color-bar>
                    <Range>
                        <Data increment="3"/>
                    </Range>
                </Plot>
            </Plots>
        </Logger>
        <HistogramLogger minimum="-0.1" number-of-bins="20" normalized="true" maximum="1.1" time-step="5">
            <Plot minimum="0" maximum="1.0" terminal="png"/>
            <Column celltype="cells" symbol-ref="X"/>
            <Column celltype="cells" symbol-ref="Y"/>
        </HistogramLogger>
        <HistogramLogger minimum="0.0" number-of-bins="30" normalized="true" maximum="30" time-step="-1">
            <Plot minimum="0" maximum="1.0" terminal="png"/>
            <Column celltype="cells" symbol-ref="tau"/>
        </HistogramLogger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## MAPK_SBML

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>BIOMD0000000010</Title>
        <Details>Imported SBML model: http://www.ebi.ac.uk/biomodels-main/BIOMD0000000010
        
Kholodenko BN, Negative feedback and ultrasensitivity can bring about oscillations in the mitogen-activated protein kinase cascades.</Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="linear">
            <Size value="1, 0, 0" symbol="size"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="1.0" symbol="stop"/>
        <TimeSymbol name="time" symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="sbml_ct">
            <System time-scaling="4000" time-step="stop" solver="Dormand-Prince [adaptive, O(5)]">
                <Constant value="2.5" symbol="V1"/>
                <Constant value="9" symbol="Ki"/>
                <Constant value="1" symbol="n"/>
                <Constant value="10" symbol="K1"/>
                <DiffEqn name="gained from reactions" symbol-ref="MKKK">
                    <Expression> - V1 * MKKK / ((1 + pow(MAPK_PP / Ki, n)) * (K1 + MKKK)) + V2 * MKKK_P / (KK2 + MKKK_P)</Expression>
                </DiffEqn>
                <DiffEqn name="gained from reactions" symbol-ref="MKKK_P">
                    <Expression>V1 * MKKK / ((1 + pow(MAPK_PP / Ki, n)) * (K1 + MKKK)) - V2 * MKKK_P / (KK2 + MKKK_P)</Expression>
                </DiffEqn>
                <Constant value="0.25" symbol="V2"/>
                <Constant value="8" symbol="KK2"/>
                <Constant value="0.025" symbol="k3"/>
                <Constant value="15" symbol="KK3"/>
                <DiffEqn name="gained from reactions" symbol-ref="MKK">
                    <Expression> - k3 * MKKK_P * MKK / (KK3 + MKK) + V6 * MKK_P / (KK6 + MKK_P)</Expression>
                </DiffEqn>
                <DiffEqn name="gained from reactions" symbol-ref="MKK_P">
                    <Expression>k3 * MKKK_P * MKK / (KK3 + MKK) - uVol * k4 * MKKK_P * MKK_P / (KK4 + MKK_P) + uVol * V5 * MKK_PP / (KK5 + MKK_PP) - V6 * MKK_P / (KK6 + MKK_P)</Expression>
                </DiffEqn>
                <Constant value="0.025" symbol="k4"/>
                <Constant value="15" symbol="KK4"/>
                <DiffEqn name="gained from reactions" symbol-ref="MKK_PP">
                    <Expression>k4 * MKKK_P * MKK_P / (KK4 + MKK_P) - V5 * MKK_PP / (KK5 + MKK_PP)</Expression>
                </DiffEqn>
                <Constant value="0.75" symbol="V5"/>
                <Constant value="15" symbol="KK5"/>
                <Constant value="0.75" symbol="V6"/>
                <Constant value="15" symbol="KK6"/>
                <Constant value="0.025" symbol="k7"/>
                <Constant value="15" symbol="KK7"/>
                <DiffEqn name="gained from reactions" symbol-ref="MAPK">
                    <Expression> - k7 * MKK_PP * MAPK / (KK7 + MAPK) + V10 * MAPK_P / (KK10 + MAPK_P)</Expression>
                </DiffEqn>
                <DiffEqn name="gained from reactions" symbol-ref="MAPK_P">
                    <Expression> k7 * MKK_PP * MAPK / (KK7 + MAPK) - k8 * MKK_PP * MAPK_P / (KK8 + MAPK_P) + uVol * V9 * MAPK_PP / (KK9 + MAPK_PP) - V10 * MAPK_P / (KK10 + MAPK_P)</Expression>
                </DiffEqn>
                <Constant value="0.025" symbol="k8"/>
                <Constant value="15" symbol="KK8"/>
                <DiffEqn name="gained from reactions" symbol-ref="MAPK_PP">
                    <Expression>k8 * MKK_PP * MAPK_P / (KK8 + MAPK_P) - V9 * MAPK_PP / (KK9 + MAPK_PP)</Expression>
                </DiffEqn>
                <Constant value="0.5" symbol="V9"/>
                <Constant value="15" symbol="KK9"/>
                <Constant value="0.5" symbol="V10"/>
                <Constant value="15" symbol="KK10"/>
            </System>
            <Constant name="compartment size" value="1" symbol="uVol"/>
            <Property name="Mos" value="90" symbol="MKKK"/>
            <Property name="Mos-P" value="10" symbol="MKKK_P"/>
            <Property name="Mek1" value="280" symbol="MKK"/>
            <Property name="Mek1-P" value="10" symbol="MKK_P"/>
            <Property name="Mek1-PP" value="10" symbol="MKK_PP"/>
            <Property name="Erk2" value="280" symbol="MAPK"/>
            <Property name="Erk2-P" value="10" symbol="MAPK_P"/>
            <Property name="Erk2-PP" value="10" symbol="MAPK_PP"/>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="1" type="sbml_ct"/>
    </CellPopulations>
    <Analysis>
        <Logger time-step="stop/200">
            <Restriction>
                <Celltype celltype="sbml_ct"/>
            </Restriction>
            <Input>
                <Symbol symbol-ref="MAPK"/>
                <Symbol symbol-ref="MAPK_P"/>
                <Symbol symbol-ref="MAPK_PP"/>
                <Symbol symbol-ref="MKK"/>
                <Symbol symbol-ref="MKK_P"/>
                <Symbol symbol-ref="MKK_PP"/>
                <Symbol symbol-ref="MKKK"/>
                <Symbol symbol-ref="MKKK_P"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style grid="true" style="lines" line-width="3.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="MAPK"/>
                        <Symbol symbol-ref="MAPK_P"/>
                        <Symbol symbol-ref="MAPK_PP"/>
                        <Symbol symbol-ref="MKK"/>
                        <Symbol symbol-ref="MKK_P"/>
                        <Symbol symbol-ref="MKK_PP"/>
                        <Symbol symbol-ref="MKKK"/>
                        <Symbol symbol-ref="MKKK_P"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## PredatorPrey

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-PredatorPrey</Title>
        <Details>Example showing Predator-prey model by Rosenzweig.

The Rosenzweig model is the Lotka-Volterra model with logistic growth and type 2 functional response. 

Reference:
Rosenzweig, Michael. 1971. "The Paradox of Enrichment" Science Vol. 171: pp. 385–387


Illustrates how to 
- create a simple ODE model
- log and plot data as time course</Details>
    </Description>
    <Global>
        <Variable value="0.1" symbol="N"/>
        <Variable value="0.5" symbol="P"/>
        <System time-step="0.1" solver="Runge-Kutta [fixed, O(4)]">
            <Constant name="halftime" value="0.5" symbol="a"/>
            <Constant name="growth rate" value="0.1" symbol="r"/>
            <Constant name="consumption rate" value="0.1" symbol="c"/>
            <Constant name="conversion rate" value="0.05" symbol="b"/>
            <Constant name="mortality rate" value="0.01" symbol="m"/>
            <Constant name="Carrying capacity" value="0.8" symbol="K"/>
            <DiffEqn symbol-ref="N">
                <Expression>r*N*(1-N/K) - c*N / (a+N)*P
</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="P">
                <Expression>b*N / (a+N)*P - m*P</Expression>
            </DiffEqn>
            <!--    <Disabled>
        <Function symbol="c">
            <Expression>0.1 + time*0.00001</Expression>
        </Function>
    </Disabled>
-->
        </System>
        <Event trigger="when true" time-step="1">
            <Condition>N &lt; 0.001</Condition>
            <Rule symbol-ref="N">
                <Expression>0</Expression>
            </Rule>
        </Event>
    </Global>
    <Space>
        <Lattice class="linear">
            <Size value="1, 0, 0" symbol="size"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="5000" symbol="stoptime"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Logger time-step="5">
            <Input>
                <Symbol symbol-ref="N"/>
                <Symbol symbol-ref="P"/>
            </Input>
            <Output>
                <TextOutput file-format="csv"/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style style="lines" line-width="2.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="N"/>
                        <Symbol symbol-ref="P"/>
                    </Y-axis>
                </Plot>
                <Plot time-step="-1">
                    <Style style="lines" line-width="2.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="N"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="P"/>
                    </Y-axis>
                    <Color-bar palette="rainbow">
                        <Symbol symbol-ref="time"/>
                    </Color-bar>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```
