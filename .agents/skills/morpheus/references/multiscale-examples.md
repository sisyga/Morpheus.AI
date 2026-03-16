# Multiscale Model Examples

Reference MorpheusML v4 XML models for multiscale simulations.

---

## AutocrineChemotaxis

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-AutocrineChemotaxis</Title>
        <Details></Details>
    </Description>
    <Global>
        <Field value="0" name="chemoattractant" symbol="U">
            <Diffusion rate="0.1"/>
        </Field>
        <System solver="Euler [fixed, O(1)]" time-step="10.0">
            <DiffEqn symbol-ref="U">
                <Expression>p - d*U</Expression>
            </DiffEqn>
            <Constant value="0.01" name="degradation U" symbol="d"/>
        </System>
        <Constant value="0.003" symbol="cell_density"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="200, 200, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <NodeLength value="1.0"/>
            <Neighborhood>
                <Distance>2.5</Distance>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2.5e4"/>
        <SaveInterval value="0"/>
        <RandomSeed value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <!--    <Disabled>
        <Property value="1.0" symbol="cell"/>
    </Disabled>
-->
            <Property value="100.0" name="chemotactic strength" symbol="c"/>
            <Property value="0.01" name="production chemoattractant" symbol="p"/>
            <Property value="0" name="number of neighboring cells" symbol="neighbors"/>
            <VolumeConstraint target="60" strength="1"/>
            <SurfaceConstraint target="0.85" mode="aspherity" strength="1"/>
            <Chemotaxis contact-inhibition="false" field="U" retraction="true" strength="c"/>
            <NeighborhoodReporter>
                <Input value="cell.type == celltype.cells.id" scaling="cell"/>
                <Output mapping="sum" symbol-ref="neighbors"/>
            </NeighborhoodReporter>
        </CellType>
        <CellType name="medium" class="medium">
            <Constant value="0.0" symbol="neighbors"/>
            <Constant value="0.0" name="production" symbol="p"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0.0">
            <Contact value="-10" type1="cells" type2="medium"/>
            <Contact value="-20" type1="cells" type2="cells"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1.0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="10.0"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>2.5</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitRectangle number-of-cells="cell_density * size.x * size.y" mode="regular">
                <Dimensions size="size.x, size.y, 0" origin="0.0, 0.0, 0.0"/>
            </InitRectangle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter decorate="false" time-step="500">
            <Terminal name="png" persist="true"/>
            <Plot>
                <Field isolines="5" symbol-ref="U" surface="true" min="0.0"/>
                <Cells opacity="0.55" value="cell.type">
                    <ColorMap>
                        <Color value="2.0" color="gray"/>
                        <Color value="0" color="gray"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <ModelGraph format="svg" reduced="true"  include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```

## CellCycle

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellCycle</Title>
        <Details>ODE model of Xenopus oocyte cell cycle adopted from:

James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006</Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="hexagonal">
            <Size value="250, 250, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="1"/>
        <TimeSymbol symbol="time"/>
        <RandomSeed value="3445"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <Property value="0" name="Cyclin-dependent kinase 1" symbol="CDK1"/>
            <Property value="0" name="Polo-like kinase 1" symbol="Plk1"/>
            <Property value="0" name="Anaphase-promoting complex" symbol="APC"/>
            <System time-step="4e-2" solver="Runge-Kutta [fixed, O(4)]" time-scaling="20">
                <DiffEqn symbol-ref="CDK1">
                    <Expression>α1 - β1 * CDK1 * (APC^n / (K^n + APC^n))</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="Plk1">
                    <Expression>α2*(1-Plk1) * ((CDK1^n) / (K^n + CDK1^n)) - β2*Plk1</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="APC">
                    <Expression>α3*(1- APC) * ((Plk1^n) / (K^n + Plk1^n)) - β3*APC</Expression>
                </DiffEqn>
                <Constant value="8" name="Hill coefficient" symbol="n"/>
                <Constant value="0.5" name="Michaelis constant" symbol="K"/>
                <Constant value="0.1" symbol="α1"/>
                <Constant value="3.0" symbol="α2"/>
                <Constant value="3.0" symbol="α3"/>
                <Constant value="3.0" symbol="β1"/>
                <Constant value="1.0" symbol="β2"/>
                <Constant value="1.0" symbol="β3"/>
            </System>
            <Property value="0" name="portion" symbol="p"/>
            <Property value="0" name="divisions" symbol="d"/>
            <Property value="0" name="division timeout" symbol="c"/>
            <Property value="1" name="cellcount" symbol="cc"/>
            <Property value="25000" name="Target volume" symbol="Vt"/>
            <VolumeConstraint target="Vt" strength="1"/>
            <SurfaceConstraint mode="aspherity" target="1.0" strength="1"/>
            <Event>
                <Condition>CDK1&lt;0.2</Condition>
                <Rule symbol-ref="c">
                    <Expression>0</Expression>
                </Rule>
            </Event>
            <CellDivision division-plane="minor">
                <Condition>if(CDK1 > 0.5 and c == 0, 1, 0)</Condition>
                <Triggers>
                    <Rule symbol-ref="d">
                        <Expression>d+0.5</Expression>
                    </Rule>
                    <Rule symbol-ref="c">
                        <Expression>1</Expression>
                    </Rule>
                    <Rule symbol-ref="Vt">
                        <Expression>Vt/2</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact value="-20" type1="cells" type2="cells"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="5e-5"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="10" yield="0.1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellObjects mode="order">
                <Arrangement displacements="1, 1, 1" repetitions="1, 1, 1">
                    <Sphere radius="40" center="125,100,0"/>
                </Arrangement>
            </InitCellObjects>
            <InitProperty symbol-ref="CDK1">
                <Expression>0.25</Expression>
            </InitProperty>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="0.05" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="CDK1">
                    <ColorMap>
                        <Color value="0.5" color="red"/>
                        <Color value="0.2" color="yellow"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <Logger time-step="2e-3">
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
                    <Style line-width="4.0" style="points"/>
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
                    <Style line-width="4.0" style="points"/>
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
            <Restriction>
                <Celltype celltype="cells"/>
            </Restriction>
        </Logger>
        <ModelGraph include-tags="#untagged" reduced="false" format="svg"/>
    </Analysis>
</MorpheusModel>
```

## CellCycle_3D

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellCycle</Title>
        <Details>ODE model of Xenopus oocyte cell cycle adopted from:

James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006 
</Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="cubic">
            <Size value="100,100,100" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
                <Condition boundary="z" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="1"/>
        <TimeSymbol symbol="time"/>
        <RandomSeed value="3445"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <Property value="0" name="Cyclin-dependent kinase 1" symbol="CDK1"/>
            <Property value="0" name="Polo-like kinase 1" symbol="Plk1"/>
            <Property value="0" name="Anaphase-promoting complex" symbol="APC"/>
            <System solver="Runge-Kutta [fixed, O(4)]" time-step="4e-2" time-scaling="20">
                <DiffEqn symbol-ref="CDK1">
                    <Expression>α1 - β1 * CDK1 * (APC^n / (K^n + APC^n))</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="Plk1">
                    <Expression>α2*(1-Plk1) * ((CDK1^n) / (K^n + CDK1^n)) - β2*Plk1</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="APC">
                    <Expression>α3*(1- APC) * ((Plk1^n) / (K^n + Plk1^n)) - β3*APC</Expression>
                </DiffEqn>
                <Constant value="8" name="Hill coefficient" symbol="n"/>
                <Constant value="0.5" name="Michaelis constant" symbol="K"/>
                <Constant value="0.1" symbol="α1"/>
                <Constant value="3.0" symbol="α2"/>
                <Constant value="3.0" symbol="α3"/>
                <Constant value="3.0" symbol="β1"/>
                <Constant value="1.0" symbol="β2"/>
                <Constant value="1.0" symbol="β3"/>
            </System>
            <Property value="0" name="portion" symbol="p"/>
            <Property value="0" name="divisions" symbol="d"/>
            <Property value="0" name="division timeout" symbol="c"/>
            <Property value="1" name="cellcount" symbol="cc"/>
            <Property value="100000" name="Target volume" symbol="Vt"/>
            <VolumeConstraint target="Vt" strength="1"/>
            <SurfaceConstraint target="1.2" mode="aspherity" strength="1"/>
            <Event>
                <Condition>CDK1&lt;0.2</Condition>
                <Rule symbol-ref="c">
                    <Expression>0</Expression>
                </Rule>
            </Event>
            <CellDivision division-plane="minor">
                <Condition>if(CDK1 > 0.5 and c == 0, 1, 0)</Condition>
                <Triggers>
                    <Rule symbol-ref="d">
                        <Expression>d+0.5</Expression>
                    </Rule>
                    <Rule symbol-ref="c">
                        <Expression>1</Expression>
                    </Rule>
                    <Rule symbol-ref="Vt">
                        <Expression>Vt/2</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact value="-20" type1="cells" type2="cells"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="5e-5"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="10" yield="0.1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellObjects mode="order">
                <Arrangement displacements="1, 1, 1" repetitions="1, 1, 1">
                    <Sphere radius="25" center="50,50,50"/>
                </Arrangement>
            </InitCellObjects>
            <InitProperty symbol-ref="CDK1">
                <Expression>0.25</Expression>
            </InitProperty>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter decorate="false" time-step="0.05">
            <Terminal name="png"/>
            <Plot slice="50">
                <Cells value="CDK1">
                    <ColorMap>
                        <Color value="0.5" color="red"/>
                        <Color value="0.2" color="yellow"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <Logger time-step="2e-3">
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
                    <Style style="points" line-width="4.0"/>
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
                    <Style style="points" line-width="4.0"/>
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
            <Restriction>
                <Celltype celltype="cells"/>
            </Restriction>
        </Logger>
        <TiffPlotter format="16bit" compression="false" time-step="0.025" timelapse="true" OME-header="true">
            <Channel no-outline="true" symbol-ref="cell.id" celltype="cells"/>
            <Channel symbol-ref="CDK1" celltype="cells"/>
        </TiffPlotter>
        <ModelGraph format="svg" reduced="false" exclude-symbols="cell.id" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```

## CellCycle_PDE

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellCycle-MultiScale</Title>
        <Details>- NOTE: cell Property 'dist' does not give correct values (see Logger): values are identical for all cells!


ODE model of Xenopus oocyte cell cycle adopted from:

James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006</Details>
    </Description>
    <Global>
        <Field symbol="g" value="0">
            <Diffusion rate="100"/>
        </Field>
        <System solver="Runge-Kutta [fixed, O(4)]" time-step="0.1">
            <DiffEqn symbol-ref="g">
                <Expression>APC - 0.05*g</Expression>
            </DiffEqn>
        </System>
        <Constant symbol="CDK1" value="0.0"/>
        <Constant symbol="APC" value="0.0"/>
        <Constant symbol="Plk1" value="0.0"/>
        <Constant symbol="dist" value="0.0"/>
        <Constant symbol="posx" value="0.0"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="250, 250, 0"/>
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
        <StopTime value="2"/>
        <TimeSymbol symbol="t"/>
        <RandomSeed value="3445"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <Property name="Cyclin-dependent kinase 1" symbol="CDK1" value="0"/>
            <Property name="Polo-like kinase 1" symbol="Plk1" value="0"/>
            <Property name="Anaphase-promoting complex" symbol="APC" value="0"/>
            <System time-scaling="15" solver="Dormand-Prince [adaptive, O(5)]">
                <DiffEqn symbol-ref="CDK1">
                    <Expression>α1+(g_l) - β1 * CDK1 * (APC^n / (K^n + APC^n))</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="Plk1">
                    <Expression>α2*(1-Plk1) * ((CDK1^n) / (K^n + CDK1^n)) - β2*Plk1</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="APC">
                    <Expression>α3*(1- APC) * ((Plk1^n) / (K^n + Plk1^n)) - β3*APC</Expression>
                </DiffEqn>
                <Constant name="Hill coefficient" symbol="n" value="8"/>
                <Constant name="Michaelis constant" symbol="K" value="0.5"/>
                <Constant symbol="α1" value="0.1"/>
                <Constant symbol="α2" value="3.0"/>
                <Constant symbol="α3" value="3.0"/>
                <Constant symbol="β1" value="3.0"/>
                <Constant symbol="β2" value="1.0"/>
                <Constant symbol="β3" value="1.0"/>
            </System>
            <Property name="divisions" symbol="d" value="0"/>
            <Property name="Target volume" symbol="Vt" value="25000"/>
            <VolumeConstraint strength="1" target="Vt"/>
            <SurfaceConstraint strength="0.5" target="1.0" mode="aspherity"/>
            <Property symbol="g_l" value="0.0"/>
            <CellDivision division-plane="minor" trigger="on-change">
                <Condition>CDK1 > 0.5 and cell.volume > 100</Condition>
                <Triggers>
                    <Rule symbol-ref="d">
                        <Expression>d+0.5</Expression>
                    </Rule>
                    <Rule symbol-ref="Vt">
                        <Expression>Vt/2</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
            <Property symbol="dist" value="sqrt( (cell.center.x-size.x/2)^2 + (cell.center.y-size.y/2)^2 )  "/>
            <Mapper name="report field">
                <Input value="g"/>
                <Output symbol-ref="g_l" mapping="average"/>
            </Mapper>
        </CellType>
        <CellType name="Medium" class="medium">
            <Property name="Anaphase-promoting complex" symbol="APC" value="0"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact type1="cells" value="-12" type2="cells"/>
            <Contact type1="cells" value="0" type2="Medium"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1e-4"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="2" yield="0.1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="cells" size="0">
            <InitCellObjects mode="order">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Sphere radius="45" center="125, 110, 0"/>
                </Arrangement>
            </InitCellObjects>
            <InitProperty symbol-ref="CDK1">
                <Expression>0.25</Expression>
            </InitProperty>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="0.1" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="APC" opacity="0.5">
                    <ColorMap>
                        <Color color="blue" value="0.5"/>
                        <Color color="white" value="0.25"/>
                    </ColorMap>
                </Cells>
                <Field isolines="5" symbol-ref="g" coarsening="2" min="0.0">
                    <ColorMap>
                        <Color color="red" value="1.0"/>
                        <Color color="yellow" value="0.5"/>
                        <Color color="white" value="0.0"/>
                    </ColorMap>
                </Field>
            </Plot>
        </Gnuplotter>
        <Logger time-step="0.002">
            <Input>
                <!--    <Disabled>
        <Symbol symbol-ref="APC"/>
    </Disabled>
-->
                <!--    <Disabled>
        <Symbol symbol-ref="CDK1"/>
    </Disabled>
-->
                <!--    <Disabled>
        <Symbol symbol-ref="Plk1"/>
    </Disabled>
-->
                <Symbol symbol-ref="dist"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <!--    <Disabled>
        <Plots>
            <Plot time-step="0.25">
                <Style style="points"/>
                <Terminal terminal="png"/>
                <X-axis>
                    <Symbol symbol-ref="t"/>
                </X-axis>
                <Y-axis>
                    <Symbol symbol-ref="APC"/>
                </Y-axis>
                <Color-bar>
                    <Symbol symbol-ref="dist"/>
                </Color-bar>
            </Plot>
        </Plots>
    </Disabled>
-->
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## CellPolarity

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellPolarity</Title>
        <Details>Chemotaxis of polarized cell
----------------------------
Show feedback between cell motility, cell polarization and external gradient.
 
Two cell polarization models are taken from the original publication:
Y. Mori, A. Jilkine and L. Edelstein-Keshet (2008). Wave-Pinning and Cell Polarity from a Bistable Reaction-Diffusion System. Biophysical Journal 94(9), 3684-3697. DOI:10.1529/biophysj.107.120824

and can be enabled/disabled for a cell in 3D through the respective System in the Celltype 'cells':
- Substrate-depletion model: no repolarization
- Wave-pinning model: repolarization (as studied in detail in the above publication)
 
Events in Global:
- Switch on/off and change gradients (noise through global constant)</Details>
    </Description>
    <Global>
        <Field symbol="U" value="noisy(l.x / lattice.x)">
            <Diffusion rate="0.0"/>
        </Field>
        <Event trigger="on-change" time-step="100">
            <Condition>time>=1000</Condition>
            <Rule symbol-ref="U">
                <Expression>noisy(0.5)</Expression>
            </Rule>
        </Event>
        <Event trigger="on-change" time-step="100">
            <Condition>time>=1500</Condition>
            <Rule symbol-ref="U">
                <Expression>noisy((lattice.x-l.x) / lattice.x)</Expression>
            </Rule>
        </Event>
        <Constant symbol="l_U" value="0.0"/>
        <Constant symbol="lengthscale" value="3"/>
        <Constant symbol="noise" value="0.2"/>
        <Function symbol="noisy">
            <Parameter symbol="v" name="value"/>
            <Expression>max(0,(v+rand_norm(0,noise)))</Expression>
        </Function>
    </Global>
    <Space>
        <Lattice class="cubic">
            <Size symbol="lattice" value="150, 75, 30"/>
            <BoundaryConditions>
                <Condition type="noflux" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
                <Condition type="constant" boundary="z"/>
            </BoundaryConditions>
            <NodeLength value="1.0"/>
            <Neighborhood>
                <Distance>2.0</Distance>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="l"/>
        <MembraneLattice>
            <Resolution symbol="memsize" value="50"/>
            <SpaceSymbol symbol="m"/>
        </MembraneLattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2500"/>
        <SaveInterval value="0"/>
        <RandomSeed value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <VolumeConstraint target="5000" strength="0.1"/>
            <SurfaceConstraint target="1" strength="0.02" mode="aspherity"/>
            <MembraneProperty symbol="A" name="A" value="1.5 + rand_uni(-0.1,0.1)">
                <Diffusion rate="0.05*lengthscale^2"/>
            </MembraneProperty>
            <MembraneProperty symbol="B" name="B" value="0.8">
                <Diffusion rate="10*lengthscale^2"/>
            </MembraneProperty>
            <MembraneProperty symbol="c" name="chemotactic strength" value="0">
                <Diffusion rate="0"/>
            </MembraneProperty>
            <MembraneProperty symbol="s" name="signal" value="0">
                <Diffusion rate="0"/>
            </MembraneProperty>
            <System time-step="0.05" name="WavePinning" solver="Dormand-Prince [adaptive, O(5)]">
                <Constant symbol="k_0" value="0.067"/>
                <Constant symbol="gamma" value="1"/>
                <Constant symbol="delta" value="1"/>
                <Constant symbol="K" value="1"/>
                <!--    <Disabled>
        <Constant symbol="sigma" name="spatial-length-signal" value="5.0"/>
    </Disabled>
-->
                <Constant symbol="n" name="Hill coefficient" value="2"/>
                <Intermediate symbol="F" value="B*(k_0+ 0.2*(s-U.mean) + (gamma*A^n) / (K^n + A^n) ) - delta*A"/>
                <DiffEqn symbol-ref="A">
                    <Expression>F</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="B">
                    <Expression>-F</Expression>
                </DiffEqn>
                <Rule symbol-ref="c">
                    <Expression>A^2*1000</Expression>
                </Rule>
            </System>
            <Mapper name="Sensing the field">
                <Input value="U"/>
                <Output symbol-ref="s" mapping="average"/>
            </Mapper>
            <PropertyVector symbol="p" name="polarity" value="0.0, 0.0, 0.0"/>
            <Mapper name="Polarity extraction from membrane">
                <Input value="A"/>
                <Polarity symbol-ref="p"/>
            </Mapper>
            <DirectedMotion strength="0.04" direction="p"/>
            <!--    <Disabled>
        <System time-step="0.05" name="Substrate-Depletion(ASDM)" solver="Dormand-Prince [adaptive, O(5)]">
            <Rule symbol-ref="c">
                <Expression>A^2*5e1</Expression>
            </Rule>
            <DiffEqn symbol-ref="A">
                <Expression>B*(s.norm*A^2/(1+s_a*A^2)) - r_a * A</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="B">
                <Expression>b_b - B*(s.norm*A^2/(1+s_a*A^2)) - r_b*B</Expression>
            </DiffEqn>
            <Constant symbol="s_a" value="0.1"/>
            <Constant symbol="r_a" value="0.1"/>
            <Constant symbol="b_b" value="0.15"/>
            <Constant symbol="r_b" value="0.0"/>
            <Function symbol="s.norm">
                <Expression>0.1+0.01*(s-U.mean)/U.mean</Expression>
            </Function>
            <Disabled>
                <Constant symbol="s.norm" value="0.1"/>
            </Disabled>
        </System>
    </Disabled>
-->
            <Property symbol="U.mean" value="0.0"/>
            <Mapper name="scalar signal average over whole cell">
                <Input value="U"/>
                <Output symbol-ref="U.mean" mapping="average"/>
            </Mapper>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0.0"/>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics yield="0.05" temperature="1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>6</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="cells" size="0">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Sphere center="25 37 15" radius="10"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="50">
            <Terminal name="png"/>
            <Plot slice="15">
                <Field symbol-ref="U"/>
                <Cells min="0.2" value="A"/>
                <CellArrows orientation="p * 50"/>
            </Plot>
        </Gnuplotter>
        <TiffPlotter time-step="100" format="8bit" OME-header="false">
            <Channel symbol-ref="cell.id" celltype="cells"/>
            <Channel symbol-ref="c" celltype="cells"/>
            <Channel symbol-ref="U"/>
        </TiffPlotter>
        <Logger time-step="50">
            <Input>
                <Symbol symbol-ref="A"/>
            </Input>
            <Output>
                <TextOutput file-format="matrix"/>
            </Output>
            <Plots>
                <SurfacePlot time-step="50">
                    <Color-bar>
                        <Symbol symbol-ref="A"/>
                    </Color-bar>
                    <Terminal terminal="png"/>
                </SurfacePlot>
            </Plots>
            <Restriction>
                <Celltype celltype="cells"/>
            </Restriction>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## CellPolarity_3D

```xml
<MorpheusModel version="5">
    <Description>
        <Title>Example-CellPolarity</Title>
        <Details>Chemotaxis of polarized cell
----------------------------
Show feedback between cell motility, cell polarization and external gradient.
 
Two simple polarization models can be enabled/disabled:
- Substrate-depletion model: no repolarization
- Wave-pinning model: repolarization
 
PDE Equation:
- Switch on/off and change gradients </Details>
    </Description>
    <Global>
        <Field value="l.x / lattice.x + rand_norm(0,0.2)" symbol="U"/>
        <!--    <Disabled>
        <Equation symbol-ref="U">
            <Expression>l.x / lattice.x +
0*if( t > 500 and t &lt; 1500, l.x / lattice.x, 0)</Expression>
        </Equation>
    </Disabled>
-->
        <Constant value="0.0" symbol="c"/>
        <!--    <Disabled>
        <Constant value="0.0" symbol="A"/>
    </Disabled>
-->
    </Global>
    <Space>
        <Lattice class="cubic">
            <Size value="150, 75, 50" symbol="lattice"/>
            <BoundaryConditions>
                <Condition boundary="x" type="noflux"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <NodeLength value="1.0"/>
            <Neighborhood>
                <Distance>2.0</Distance>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="l"/>
        <MembraneLattice>
            <Resolution value="50" symbol="memsize"/>
            <SpaceSymbol symbol="m"/>
        </MembraneLattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2000"/>
        <SaveInterval value="0"/>
        <RandomSeed value="0"/>
        <TimeSymbol symbol="t"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <VolumeConstraint target="5000" strength="0.1"/>
            <SurfaceConstraint mode="aspherity" target="1" strength="0.05"/>
            <MembraneProperty name="A" value="0.5" symbol="A"/>
            <MembraneProperty name="B" value="0.5" symbol="B"/>
            <MembraneProperty name="chemotactic strength" value="0" symbol="c"/>
            <MembraneProperty name="signal" value="0" symbol="s"/>
            <Property value="0" symbol="l_U"/>
            <!--    <Disabled>
        <System solver="Dormand-Prince [adaptive, O(5)]" name="Substrate-Depletion">
            <Rule symbol-ref="c">
                <Expression>A^2*5e1</Expression>
            </Rule>
            <DiffEqn symbol-ref="A">
                <Reaction>(rho*A^2) / B - mu_a * A + rho_a + 0.01*s
</Reaction>
                <Diffusion>0.05</Diffusion>
            </DiffEqn>
            <DiffEqn symbol-ref="B">
                <Reaction>(rho*A^2) - mu_i * B
</Reaction>
                <Diffusion>0.2</Diffusion>
            </DiffEqn>
            <Constant value="0.01" symbol="rho_a"/>
            <Constant value="0.03" symbol="mu_i"/>
            <Constant value="0.02" symbol="mu_a"/>
            <Constant value="0.001" symbol="rho"/>
        </System>
    </Disabled>
-->
            <System solver="Dormand-Prince [adaptive, O(5)]" name="WavePinning">
                <Constant value="0.067" symbol="k_0"/>
                <Constant value="1" symbol="gamma"/>
                <Constant value="0.25" symbol="delta"/>
                <Constant value="1" symbol="K"/>
                <Constant name="spatial-length-signal" value="5.0" symbol="sigma"/>
                <Constant name="Hill coefficient" value="4" symbol="n"/>
                <Intermediate value="B*(k_0+ s + (gamma*A^n) / (K^n + A^n) ) - delta*A" symbol="F"/>
                <DiffEqn symbol-ref="A">
                    <Reaction>F</Reaction>
                    <Diffusion>0.05</Diffusion>
                </DiffEqn>
                <DiffEqn symbol-ref="B">
                    <Reaction>-F</Reaction>
                    <Diffusion>1</Diffusion>
                </DiffEqn>
                <Rule symbol-ref="c">
                    <Expression>A^2*1000</Expression>
                </Rule>
            </System>
            <Mapper>
                <Input value="U"/>
                <Output mapping="average" symbol-ref="s"/>
            </Mapper>
            <PropertyVector value="0.0, 0.0, 0.0" symbol="dir"/>
            <Mapper>
                <Input value="A"/>
                <Polarity symbol-ref="dir"/>
            </Mapper>
            <DirectedMotion direction="dir" strength="0.5 * dir.abs / (1+dir.abs)"/>
        </CellType>
        <CellType name="medium" class="medium">
            <Property value="0" symbol="l_U"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0.0">
            <Contact type2="medium" type1="cells" value="-10"/>
            <Contact type2="cells" type1="cells" value="-20"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="1" yield="0.05"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>6</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Sphere center="25, 37, 25" radius="10.0"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="50">
            <Terminal name="png"/>
            <Plot slice="25">
                <Field symbol-ref="U"/>
                <Cells value="A"/>
                <CellArrows orientation="dir * 100"/>
            </Plot>
        </Gnuplotter>
        <TiffPlotter format="8bit" OME-header="false" time-step="100">
            <Channel celltype="cells" symbol-ref="cell.id"/>
            <Channel celltype="cells" symbol-ref="c"/>
            <Channel symbol-ref="U"/>
        </TiffPlotter>
        <Logger time-step="50">
            <Input>
                <Symbol symbol-ref="A"/>
            </Input>
            <Output>
                <TextOutput file-format="matrix"/>
            </Output>
            <Plots>
                <SurfacePlot time-step="50">
                    <Color-bar>
                        <Symbol symbol-ref="A"/>
                    </Color-bar>
                    <Terminal terminal="png"/>
                </SurfacePlot>
            </Plots>
            <Restriction>
                <Celltype celltype="cells"/>
            </Restriction>
        </Logger>
        <ModelGraph format="svg" reduced="false" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```

## Dictyostelium

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-Dictyostelium</Title>
        <Details>Aggregation of dictyostelium by chemotactic amoeba as excitable medium mediated by diffusive cAMP signal.

Original reference:
- Nicholas Savill and Paulien Hogeweg, Modelling morphogenesis: from single cells to crawling slugs, J. Theo. Biol., 1997.

Morpeus implementation by ECMI 2012 summer course:
- A. Quintero, M. Myllykoski, A. Igolkina, A. Freltoft, N. Dixit, F. Rost, Morphogenesis and Dynamics of Multicellular Systems, ECMI Newletter 52, 2012.</Details>
    </Description>
    <Global>
        <Field value="0" symbol="cAMP" name="cAMP" tags="signal">
            <Diffusion rate="1"/>
            <BoundaryValue boundary="x" value="0"/>
            <BoundaryValue boundary="-x" value="0"/>
            <BoundaryValue boundary="y" value="0"/>
            <BoundaryValue boundary="-y" value="0"/>
        </Field>
        <Field value="0" symbol="r" name="refractoriness">
            <Diffusion rate="0"/>
            <BoundaryValue boundary="x" value="0"/>
            <BoundaryValue boundary="-x" value="0"/>
            <BoundaryValue boundary="y" value="0"/>
            <BoundaryValue boundary="-y" value="0"/>
        </Field>
        <System time-step="0.1" solver="Heun [fixed, O(2)]" tags="signal">
            <Constant value="0.006" symbol="c1"/>
            <Constant value="0.841" symbol="c2"/>
            <DiffEqn symbol-ref="cAMP">
                <Expression>is_amoeba*(-f() -r)</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="r">
                <Expression>is_amoeba*epsilon()*(3.5*cAMP-b-r)</Expression>
            </DiffEqn>
            <Function symbol="epsilon">
                <Expression>if(cAMP &lt; c1, 0.5,
 if(cAMP &lt; c2, 0.0589,
  0.5))</Expression>
            </Function>
            <Function symbol="f">
                <Expression>if(cAMP &lt; c1, 20*cAMP, 
 if(cAMP &lt; c2, -3*cAMP+0.15,
  15*(cAMP-1)))</Expression>
            </Function>
        </System>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="150, 150, 0" symbol="l"/>
            <BoundaryConditions>
                <Condition boundary="x" type="constant"/>
                <Condition boundary="-x" type="constant"/>
                <Condition boundary="y" type="constant"/>
                <Condition boundary="-y" type="constant"/>
            </BoundaryConditions>
            <NodeLength value="0.37"/>
            <Neighborhood>
                <Distance>1.5</Distance>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="750" symbol="end"/>
        <TimeSymbol symbol="time"/>
        <RandomSeed value="1357906713"/>
    </Time>
    <CellTypes>
        <CellType name="medium" class="medium">
            <Property value="0" symbol="b"/>
            <Property value="0" symbol="max_c"/>
            <Property value="0" symbol="phase"/>
            <Property value="0" symbol="is_amoeba"/>
        </CellType>
        <CellType name="amoeba" class="biological">
            <VolumeConstraint strength="1" target="40"/>
            <Chemotaxis field="cAMP" strength="if(phase == 2, 10, 0)" tags="response"/>
            <Property value="1.0" symbol="is_amoeba"/>
            <Property value="0" symbol="b"/>
            <Property value="0" symbol="max_c"/>
            <Property value="1" symbol="phase"/>
            <Property value="0" symbol="phaseTime"/>
            <Property value="0.1" symbol="phase2duration"/>
            <Function symbol="mu">
                <Expression>if(phase == 2, 10, 0)</Expression>
            </Function>
            <System time-step="1.0" solver="Euler [fixed, O(1)]" tags="response">
                <Rule symbol-ref="phaseTime">
                    <Expression>if(phase == 2, phaseTime+MCStime, 0)</Expression>
                </Rule>
                <Rule symbol-ref="phase" name="Rule_2_3">
                    <Expression>if(phase == 1 and max_c > 0.1, 2,
if(phase == 2 and phaseTime>phase2duration, 3,
if(phase == 3 and max_c &lt; 0.05, 1, 
phase
))) </Expression>
                </Rule>
            </System>
            <Mapper tags="response">
                <Input value="cAMP"/>
                <Output symbol-ref="max_c" mapping="maximum"/>
            </Mapper>
        </CellType>
        <CellType name="autoAmoeba" class="biological">
            <VolumeConstraint strength="1" target="40"/>
            <Property value="0.5" symbol="b"/>
            <Property value="0" symbol="max_c"/>
            <Property value="0" symbol="phase"/>
            <Property value="1.0" symbol="is_amoeba"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type2="amoeba" value="4" type1="amoeba"/>
            <Contact type2="medium" value="2" type1="amoeba"/>
            <Contact type2="autoAmoeba" value="4" type1="amoeba"/>
            <Contact type2="medium" value="3" type1="autoAmoeba"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="0.5" symbol="MCStime"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics yield="0.1" temperature="1.0"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>1.5</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="1" type="autoAmoeba">
            <InitRectangle number-of-cells="1" mode="regular">
                <Dimensions size="10, 10, 0" origin="l.x/2, l.y/2, 0"/>
            </InitRectangle>
        </Population>
        <Population size="1" type="amoeba">
            <InitRectangle number-of-cells="250" mode="regular">
                <Dimensions size="l.x-6,l.y-6,1" origin="3,3,0"/>
            </InitRectangle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="5" decorate="false">
            <Terminal size="400 400 0" name="png"/>
            <Plot>
                <Field symbol-ref="cAMP" min="0" max="1.0">
                    <ColorMap>
                        <Color color="white" value="0"/>
                        <Color color="yellow" value="0.5"/>
                        <Color color="red" value="1.0"/>
                    </ColorMap>
                </Field>
                <Cells opacity="0.65" min="0" value="phase" max="3">
                    <ColorMap>
                        <Color color="black" value="0"/>
                        <Color color="yellow" value="1"/>
                        <Color color="green" value="2"/>
                        <Color color="red" value="3"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <ModelGraph include-tags="signal" reduced="true" format="svg" exclude-symbols="is_amoeba"/>
    </Analysis>
</MorpheusModel>
```

## ExcitableTissue

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-ExcitableTissue</Title>
        <Details>Barkley model of excitable tissue, with intercellular diffusive coupling. CPM model is coupled to intracellular model via adhesion and target volume. 

</Details>
    </Description>
    <Global>
        <Constant value="0.0" symbol="u"/>
        <Constant value="0.0" symbol="v"/>
        <Constant value="25" name="width" symbol="w"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="400,400,0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <NodeLength value="1.0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol name="position in space" symbol="l"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="100"/>
        <SaveInterval value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Gnuplotter decorate="false" time-step="1">
            <Terminal name="png"/>
            <!--    <Disabled>
        <Plot>
            <Cells value="u">
                <ColorMap>
                    <Color value="0" color="white"/>
                    <Color value="0.5" color="yellow"/>
                    <Color value="1" color="red"/>
                </ColorMap>
            </Cells>
        </Plot>
    </Disabled>
-->
            <Plot>
                <Cells value="v">
                    <ColorMap>
                        <Color value="0" color="white"/>
                        <Color value="0.5" color="yellow"/>
                        <Color value="1" color="red"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <ModelGraph format="svg" reduced="false" include-tags="#untagged"/>
    </Analysis>
    <CellTypes>
        <CellType name="cells" class="biological">
            <Property value="0.0" symbol="u"/>
            <Property value="0.0" symbol="v"/>
            <Property value="0.0" symbol="u_n"/>
            <Property value="1.1" symbol="Du"/>
            <NeighborhoodReporter>
                <Input value="u" scaling="length"/>
                <Output mapping="average" symbol-ref="u_n"/>
            </NeighborhoodReporter>
            <System solver="Dormand-Prince [adaptive, O(5)]">
                <DiffEqn symbol-ref="u">
                    <Expression>(1/e)*u*(1-u)*(u-((v+b)/a)) + Du*(0.5*u_n - 0.5*u)</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="v">
                    <Expression>u-v</Expression>
                </DiffEqn>
                <Constant value="0.02" symbol="e"/>
                <Constant value="0.8" symbol="a"/>
                <Constant value="0.01" symbol="b"/>
            </System>
            <!--    <Disabled>
        <VolumeConstraint target="50" strength="1"/>
    </Disabled>
-->
            <VolumeConstraint target="100 - 80*v" strength="1"/>
            <SurfaceConstraint target="1" mode="aspherity" strength="1"/>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitProperty symbol-ref="u">
                <Expression>if(cell.center.x > size.x/2-w and 
   cell.center.x &lt; size.x/2+w and 
   cell.center.y > size.y/2-w and 
   cell.center.y &lt; size.y/2+w, 1, 0)</Expression>
            </InitProperty>
            <InitProperty symbol-ref="v">
                <Expression>if(cell.center.x > size.x/2 and 
   cell.center.y > size.y/2, 1, 0)</Expression>
            </InitProperty>
            <InitCellObjects mode="distance">
                <Arrangement displacements="9,9,1" repetitions="35,35,1">
                    <Sphere radius="8" center="50.0, 50.0, 0.0"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <CPM>
        <Interaction>
            <Contact value="-5" type1="cells" type2="cells">
                <HomophilicAdhesion adhesive="u" strength="-10"/>
            </Contact>
        </Interaction>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </ShapeSurface>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="0.05"/>
            <MetropolisKinetics temperature="5"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </MonteCarloSampler>
    </CPM>
</MorpheusModel>
```

## MultiscaleModel

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="1">
    <Description>
        <Title>Example-CellCycle-MultiScale</Title>
        <Details>- NOTE: cell Property 'dist' does not give correct values (see Logger): values are identical for all cells!


ODE model of Xenopus oocyte cell cycle adopted from:

James Ferrell, Tony Yu-Chen Tsai and Qiong Yang (2011) Modeling the Cell Cycle: Why Do Certain Circuits Oscillate?, Cell 144, p874-885. http://dx.doi.org/10.1016/j.cell.2011.03.006</Details>
    </Description>
    <Global>
        <Field symbol="g" value="0">
            <Diffusion rate="100"/>
        </Field>
        <System solver="runge-kutta" time-step="0.1">
            <DiffEqn symbol-ref="g">
                <Expression>APC - 0.05*g</Expression>
            </DiffEqn>
        </System>
        <Constant symbol="CDK1" value="0.0"/>
        <Constant symbol="APC" value="0.0"/>
        <Constant symbol="Plk1" value="0.0"/>
        <Constant symbol="dist" value="0.0"/>
        <Constant symbol="posx" value="0.0"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="250 250 0"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2"/>
        <TimeSymbol symbol="t"/>
        <RandomSeed value="3445"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="cells">
            <Property symbol="CDK1" value="0" name="Cyclin-dependent kinase 1"/>
            <Property symbol="Plk1" value="0" name="Polo-like kinase 1"/>
            <Property symbol="APC" value="0" name="Anaphase-promoting complex"/>
            <System solver="runge-kutta" time-scaling="15" time-step="4e-2">
                <DiffEqn symbol-ref="CDK1">
                    <Expression>α1+(g_l) - β1 * CDK1 * (APC^n / (K^n + APC^n))</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="Plk1">
                    <Expression>α2*(1-Plk1) * ((CDK1^n) / (K^n + CDK1^n)) - β2*Plk1</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="APC">
                    <Expression>α3*(1- APC) * ((Plk1^n) / (K^n + Plk1^n)) - β3*APC</Expression>
                </DiffEqn>
                <Constant symbol="n" value="8" name="Hill coefficient"/>
                <Constant symbol="K" value="0.5" name="Michaelis constant"/>
                <Constant symbol="α1" value="0.1"/>
                <Constant symbol="α2" value="3.0"/>
                <Constant symbol="α3" value="3.0"/>
                <Constant symbol="β1" value="3.0"/>
                <Constant symbol="β2" value="1.0"/>
                <Constant symbol="β3" value="1.0"/>
            </System>
            <Property symbol="d" value="0" name="divisions"/>
            <Property symbol="c" value="0" name="division timeout"/>
            <Property symbol="Vt" value="25000" name="Target volume"/>
            <VolumeConstraint target="Vt" strength="1"/>
            <SurfaceConstraint target="0.95" strength="0.5"/>
            <Event trigger="on change" name="reset timeout">
                <Condition>CDK1&lt;0.25</Condition>
                <Rule symbol-ref="c">
                    <Expression>0</Expression>
                </Rule>
            </Event>
            <Property symbol="g_l" value="0.0"/>
            <CellDivision division-plane="minor">
                <Condition>CDK1 > 0.5 and c == 0 and cell.volume > 100</Condition>
                <Triggers>
                    <Rule symbol-ref="d">
                        <Expression>d+0.5</Expression>
                    </Rule>
                    <Rule symbol-ref="c">
                        <Expression>1</Expression>
                    </Rule>
                    <Rule symbol-ref="Vt">
                        <Expression>Vt/2</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
            <CellReporter name="report field">
                <Input value="g"/>
                <Output symbol-ref="g_l" mapping="average"/>
            </CellReporter>
            <Property symbol="dist" value="sqrt( (cell.center.x-size.x/2)^2 + (cell.center.y-size.y/2)^2 )  "/>
        </CellType>
        <CellType class="medium" name="Medium">
            <Property symbol="APC" value="0" name="Anaphase-promoting complex"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact type1="cells" type2="cells" value="-12"/>
            <Contact type1="cells" type2="Medium" value="0"/>
        </Interaction>
        <MCSDuration value="1e-4"/>
        <MetropolisKinetics temperature="2" yield="0.1" stepper="edgelist">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </MetropolisKinetics>
    </CPM>
    <CellPopulations>
        <Population size="0" type="cells">
            <InitCellObjects mode="order">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Object>
                        <Sphere radius="25" center="0, 150, 0"/>
                    </Object>
                </Arrangement>
            </InitCellObjects>
            <InitProperty symbol-ref="CDK1">
                <Expression>0.25</Expression>
            </InitProperty>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter clean="true" time-step="0.1" timename="false">
            <Terminal opacity="0.5" size="400 400 0" name="png"/>
            <Plot>
                <Cells value="APC">
                    <ColorMap>
                        <Color value="0.5" color="blue"/>
                        <Color value="0.25" color="white"/>
                    </ColorMap>
                </Cells>
                <Field resolution="100" symbol-ref="g" isolines="5" min="0.0">
                    <ColorMap>
                        <Color value="1.0" color="red"/>
                        <Color value="0.5" color="yellow"/>
                        <Color value="0.0" color="white"/>
                    </ColorMap>
                </Field>
            </Plot>
        </Gnuplotter>
        <Logger time-step="0.002">
            <Input>
                <!--    <Disabled>
        <Symbol symbol-ref="APC"/>
    </Disabled>
-->
                <!--    <Disabled>
        <Symbol symbol-ref="CDK1"/>
    </Disabled>
-->
                <!--    <Disabled>
        <Symbol symbol-ref="Plk1"/>
    </Disabled>
-->
                <Symbol symbol-ref="dist"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <!--    <Disabled>
        <Plots>
            <Plot time-step="0.25">
                <Style style="points"/>
                <Terminal terminal="png"/>
                <X-axis>
                    <Symbol symbol-ref="t"/>
                </X-axis>
                <Y-axis>
                    <Symbol symbol-ref="APC"/>
                </Y-axis>
                <Color-bar>
                    <Symbol symbol-ref="dist"/>
                </Color-bar>
            </Plot>
        </Plots>
    </Disabled>
-->
        </Logger>
    </Analysis>
</MorpheusModel>
```

## PCP

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-PCP</Title>
        <Details>Planar Cell Polarity (PCP) example
The tissue size is adaptive and can be controlled via the global parameters cols, rows and R.
The random initial conditions give rise to a variety of patterning dynamics.

All dynamics are mediated through the membrane contacts of the cells.</Details>
    </Description>
    <Global>
        <Field symbol="x" value="0">
            <Diffusion rate="0.0"/>
        </Field>
        <Constant symbol="A" value="0.0"/>
        <Constant symbol="C" value="0.0"/>
        <ConstantVector symbol="polC" value="0.0, 0.0, 0.0"/>
        <Constant symbol="orientation" value="0.25"/>
        <Constant symbol="R" name="Cell radius" value="8.0"/>
        <Constant symbol="rows" name="Number of tissue rows" value="12.0"/>
        <Constant symbol="cols" name="Number of tissue columns" value="12.0"/>
        <Constant symbol="d_rows" name="Number of double rows" value="rint(rows/2)"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="2*R*cols, 4*R*d_rows, 0"/>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
            <NodeLength value="2"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <Annotation>Lattice size for square must be
   2*R*cols, 4*sin(pi/3)*R*d_rows, 0
and for hexagonal 
   2*R*cols, 4*R*d_rows, 0
, since these are given in nodes, not orthogonal extends.</Annotation>
        </Lattice>
        <SpaceSymbol symbol="l"/>
        <MembraneLattice>
            <Resolution symbol="memsize" value="24"/>
            <SpaceSymbol symbol="m"/>
        </MembraneLattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2500"/>
        <!--    <Disabled>
        <RandomSeed value="0"/>
    </Disabled>
-->
        <TimeSymbol symbol="t"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <MembraneProperty symbol="A" value="0.8">
                <!--    <Disabled>
        <Diffusion rate="100"/>
    </Disabled>
-->
                <Diffusion well-mixed="true" rate="0"/>
            </MembraneProperty>
            <MembraneProperty symbol="C" value="rand_norm(0.2,0.1)">
                <Diffusion rate="10"/>
            </MembraneProperty>
            <MembraneProperty symbol="c" name="C_nb" value="0">
                <Diffusion rate="0"/>
            </MembraneProperty>
            <System time-step="0.1" solver="Bogacki-Shampine [adaptive, O(3)]">
                <Constant symbol="dt" name="copy (repeat) value from System here" value="0.1"/>
                <Constant symbol="d" name="decay" value="0.1"/>
                <Constant symbol="h" name="cell-cell coupling" value="10"/>
                <Constant symbol="b" name="base activation" value="0.01"/>
                <Intermediate symbol="F" name="bistable, wave-pinning mechanism" value="A*(&#xa;  (1.5*(C/(1+C)) / (1+h*c^2)) &#xa;  + b&#xa;) &#xa;- d*C"/>
                <DiffEqn symbol-ref="A">
                    <Expression>-F</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="C">
                    <Expression>F</Expression>
                </DiffEqn>
            </System>
            <PropertyVector symbol="polC" value="0.0, 0.0, 0.0"/>
            <NeighborhoodReporter time-step="1.0">
                <Input scaling="length" value="C"/>
                <Output symbol-ref="c" mapping="average"/>
            </NeighborhoodReporter>
            <Property symbol="orientation" value="0.2"/>
            <Property symbol="sumC" value="0"/>
            <Mapper>
                <Input value="C"/>
                <Polarity symbol-ref="polC"/>
            </Mapper>
            <Mapper>
                <Input value="C"/>
                <Output symbol-ref="sumC" mapping="sum"/>
            </Mapper>
        </CellType>
        <CellType name="medium" class="medium"/>
    </CellTypes>
    <CellPopulations>
        <Population type="cells" size="0">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="cols, d_rows, 1" displacements="2*R, 2*sin(pi/3)*2*R, 1">
                    <Sphere center="R-0.5, 0.5+R, 0.0" radius="1.2*R"/>
                </Arrangement>
                <Arrangement repetitions="cols, d_rows, 1" displacements="2*R, 2*sin(pi/3)*2*R, 1">
                    <Sphere center="-0.5, 0.5+R+sin(pi/3)*2*R, 0.0" radius="1.2*R"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="C">
                    <ColorMap>
                        <Color color="red" value="8"/>
                        <Color color="yellow" value="2"/>
                        <Color color="white" value="0.0"/>
                    </ColorMap>
                </Cells>
                <CellArrows orientation="polC * 20.0"/>
            </Plot>
        </Gnuplotter>
        <Gnuplotter time-step="100" decorate="true">
            <Terminal name="png"/>
            <Plot>
                <Cells max="6.28" min="0.0" value="polC.phi">
                    <ColorMap>
                        <Color color="red" value="5.4"/>
                        <Color color="magenta" value="4.5"/>
                        <Color color="blue" value="3.6"/>
                        <Color color="cyan" value="2.7"/>
                        <Color color="green" value="1.8"/>
                        <Color color="yellow" value="0.9"/>
                        <Color color="red" value="0.0"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <HistogramLogger minimum="0.0" time-step="100" maximum="6.28" normalized="false" number-of-bins="36">
            <Column symbol-ref="polC.phi" celltype="cells"/>
            <Plot minimum="0.0" terminal="png"/>
        </HistogramLogger>
        <ModelGraph include-tags="#untagged" reduced="false" format="svg"/>
    </Analysis>
</MorpheusModel>
```

## PlanarCellPolarity

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-PCP</Title>
        <Details>Planar Cell Polarity (PCP) example
The tissue size is adaptive and can be controlled via the global parameters cols, rows and R.
The random initial conditions give rise to a variety of patterning dynamics.

All dynamics are mediated through the membrane contacts of the cells.</Details>
    </Description>
    <Global>
        <Field symbol="x" value="0">
            <Diffusion rate="0.0"/>
        </Field>
        <Constant symbol="A" value="0.0"/>
        <Constant symbol="C" value="0.0"/>
        <ConstantVector symbol="polC" value="0.0, 0.0, 0.0"/>
        <Constant symbol="orientation" value="0.25"/>
        <Constant symbol="R" name="Cell radius" value="8.0"/>
        <Constant symbol="rows" name="Number of tissue rows" value="12.0"/>
        <Constant symbol="cols" name="Number of tissue columns" value="12.0"/>
        <Constant symbol="d_rows" name="Number of double rows" value="rint(rows/2)"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="2*R*cols, 4*R*d_rows, 0"/>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
            <NodeLength value="2"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <Annotation>Lattice size for square must be
   2*R*cols, 4*sin(pi/3)*R*d_rows, 0
and for hexagonal 
   2*R*cols, 4*R*d_rows, 0
, since these are given in nodes, not orthogonal extends.</Annotation>
        </Lattice>
        <SpaceSymbol symbol="l"/>
        <MembraneLattice>
            <Resolution symbol="memsize" value="24"/>
            <SpaceSymbol symbol="m"/>
        </MembraneLattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2500"/>
        <!--    <Disabled>
        <RandomSeed value="0"/>
    </Disabled>
-->
        <TimeSymbol symbol="t"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <MembraneProperty symbol="A" value="0.8">
                <!--    <Disabled>
        <Diffusion rate="100"/>
    </Disabled>
-->
                <Diffusion well-mixed="true" rate="0"/>
            </MembraneProperty>
            <MembraneProperty symbol="C" value="rand_norm(0.2,0.1)">
                <Diffusion rate="10"/>
            </MembraneProperty>
            <MembraneProperty symbol="c" name="C_nb" value="0">
                <Diffusion rate="0"/>
            </MembraneProperty>
            <System time-step="0.1" solver="Bogacki-Shampine [adaptive, O(3)]">
                <Constant symbol="dt" name="copy (repeat) value from System here" value="0.1"/>
                <Constant symbol="d" name="decay" value="0.1"/>
                <Constant symbol="h" name="cell-cell coupling" value="10"/>
                <Constant symbol="b" name="base activation" value="0.01"/>
                <Intermediate symbol="F" name="bistable, wave-pinning mechanism" value="A*(&#xa;  (1.5*(C/(1+C)) / (1+h*c^2)) &#xa;  + b&#xa;) &#xa;- d*C"/>
                <DiffEqn symbol-ref="A">
                    <Expression>-F</Expression>
                </DiffEqn>
                <DiffEqn symbol-ref="C">
                    <Expression>F</Expression>
                </DiffEqn>
            </System>
            <PropertyVector symbol="polC" value="0.0, 0.0, 0.0"/>
            <NeighborhoodReporter time-step="1.0">
                <Input scaling="length" value="C"/>
                <Output symbol-ref="c" mapping="average"/>
            </NeighborhoodReporter>
            <Property symbol="orientation" value="0.2"/>
            <Property symbol="sumC" value="0"/>
            <Mapper>
                <Input value="C"/>
                <Polarity symbol-ref="polC"/>
            </Mapper>
            <Mapper>
                <Input value="C"/>
                <Output symbol-ref="sumC" mapping="sum"/>
            </Mapper>
        </CellType>
        <CellType name="medium" class="medium"/>
    </CellTypes>
    <CellPopulations>
        <Population type="cells" size="0">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="cols, d_rows, 1" displacements="2*R, 2*sin(pi/3)*2*R, 1">
                    <Sphere center="R, R, 0.0" radius="1.2*R"/>
                </Arrangement>
                <Arrangement repetitions="cols, d_rows, 1" displacements="2*R, 2*sin(pi/3)*2*R, 1">
                    <Sphere center="0, R+sin(pi/3)*2*R, 0.0" radius="1.2*R"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="C">
                    <ColorMap>
                        <Color color="red" value="8"/>
                        <Color color="yellow" value="2"/>
                        <Color color="white" value="0.0"/>
                    </ColorMap>
                </Cells>
                <CellArrows orientation="polC * 20.0"/>
            </Plot>
        </Gnuplotter>
        <Gnuplotter time-step="100" decorate="true">
            <Terminal name="png"/>
            <Plot>
                <Cells max="6.28" min="0.0" value="polC.phi">
                    <ColorMap>
                        <Color color="red" value="5.4"/>
                        <Color color="magenta" value="4.5"/>
                        <Color color="blue" value="3.6"/>
                        <Color color="cyan" value="2.7"/>
                        <Color color="green" value="1.8"/>
                        <Color color="yellow" value="0.9"/>
                        <Color color="red" value="0.0"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <HistogramLogger minimum="0.0" time-step="100" maximum="6.28" normalized="false" number-of-bins="36">
            <Column symbol-ref="polC.phi" celltype="cells"/>
            <Plot minimum="0.0" terminal="png"/>
        </HistogramLogger>
        <ModelGraph include-tags="#untagged" reduced="false" format="svg"/>
    </Analysis>
</MorpheusModel>
```

## VascularPatterning

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-VascularPatterning</Title>
        <Details>Reference:
- A Köhn-Luque, W de Back, Y Yamaguchi, K Yoshimura, M A Herrero, T Miura (2013) Dynamics of VEGF matrix-retention in vascular network patterning, Physical Biology, 10(6) : 066007
http://dx.doi.org/10.1088/1478-3975/10/6/066007

Related to:
- Köhn-Luque A, de Back W, Starruß J, Mattiotti A, Deutsch A, Perez-Pomares JM, Herrero MA (2011) Early Embryonic Vascular Patterning by Matrix-Mediated Paracrine Signalling: A Mathematical Model Study. PLoS ONE 6(9): e24175. 
http://dx.doi.org/10.1371/journal.pone.0024175

</Details>
    </Description>
    <Global>
        <Field value="1.5e-6" name="VEGF" symbol="u">
            <Diffusion rate="58.7"/>
        </Field>
        <Field value="0" name="Free ECM" symbol="s">
            <Diffusion rate="0.001"/>
        </Field>
        <Field value="0" name="VEGF_b" symbol="b">
            <Diffusion rate="0"/>
        </Field>
        <Field value="0" name="VEGF_s + VEGF_b" symbol="VEGF_all">
            <Diffusion rate="0"/>
        </Field>
        <System solver="Heun [fixed, O(2)]" time-step="5.0">
            <Constant value="5e-3" name="Production ECM" symbol="gamma"/>
            <Constant value="8.5e-4" name="Binding rate VEGF/ECM" symbol="k_on"/>
            <Constant value="3.6e-3" name="Unbinding rate VEGF/ECM" symbol="k_off"/>
            <Constant value="2.6e-6" name="Decay VEGF " symbol="delta"/>
            <DiffEqn symbol-ref="u">
                <Expression>- k_on*u*s + k_off*b - delta*u</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="s">
                <Expression>gamma*cell - k_on*u*s+k_off*b</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="b">
                <Expression>k_on*u*s - k_off*b</Expression>
            </DiffEqn>
            <Rule symbol-ref="VEGF_all">
                <Expression>u+b</Expression>
            </Rule>
        </System>
        <Constant value="0.0" symbol="cell"/>
        <Constant value="0.0045" symbol="cell_density"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="200, 200, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <NodeLength value="2"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="l"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="3600"/>
        <SaveInterval value="0"/>
        <RandomSeed value="1"/>
        <TimeSymbol symbol="t"/>
    </Time>
    <CellTypes>
        <CellType name="HUVEC" class="biological">
            <Property value="1.0" name="cell" symbol="cell"/>
            <Property value="3e7" name="chemotactic strength" symbol="str"/>
            <VolumeConstraint target="90" strength="1"/>
            <Chemotaxis contact-inhibition="false" field="b" retraction="false" strength="str"/>
            <!--    <Disabled>
        <AddCell overwrite="false">
            <Triggers/>
            <Distribution>l.x / size.x</Distribution>
            <Count>randuni(0,1) &lt; 0.24 + 0.0*t</Count>
        </AddCell>
    </Disabled>
-->
        </CellType>
        <CellType name="medium" class="medium"/>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact value="3.2" type1="medium" type2="HUVEC"/>
            <Contact value="6.4" type1="HUVEC" type2="HUVEC"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1.0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="HUVEC">
            <InitRectangle number-of-cells="cell_density * size.x * size.y" mode="regular">
                <Dimensions size="200,200,0" origin="0,0,0"/>
            </InitRectangle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter decorate="false" time-step="250">
            <Terminal name="png"/>
            <Plot>
                <Field symbol-ref="b"/>
                <Cells value="cell" opacity="0.65">
                    <ColorMap>
                        <Color value="1" color="gray"/>
                        <Color value="0.0" color="gray"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <!--    <Disabled>
        <HistogramLogger normalized="false" time-step="100" number-of-bins="10">
            <Plot terminal="png" minimum="0" maximum="1.0"/>
            <Column symbol-ref="cell.id" celltype="Angioblasts"/>
        </HistogramLogger>
    </Disabled>
-->
        <ModelGraph format="svg" reduced="true" exclude-symbols="cell,cell.center" include-tags="#untagged"/>
    </Analysis>
</MorpheusModel>
```
