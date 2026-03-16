# Cellular Potts Model (CPM) Examples

Reference MorpheusML v4 XML models for cpm simulations.

---

## CPM_Game_of_Life

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="3">
    <Description>
        <Details>CPM model with "Game of Life" rules.

1. Cells adhere to each other
2. Cells divide if &lt; 3 neighbors
3. Cells die if > 6 neighbors

These rules results in complex network formation. </Details>
        <Title>Example-CPM-GameofLife</Title>
    </Description>
    <Space>
        <Lattice class="square">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <Size symbol="size" value="500, 500, 0"/>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="50000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="cell">
            <VolumeConstraint target="100" strength="1"/>
            <SurfaceConstraint target="1" mode="aspherity" strength="1"/>
            <Property symbol="n_neighbors" value="0" name="Number of neighboring cells"/>
            <NeighborhoodReporter name="Count neighbors">
                <Input scaling="cell" value="cell.type == 0"/>
                <Output symbol-ref="n_neighbors" mapping="sum"/>
            </NeighborhoodReporter>
            <CellDivision name="Divide if less than 3 neighbors" division-plane="minor">
                <Condition>n_neighbors &lt; 3 and  rand_uni(0,1) &lt; 0.015</Condition>
                <Triggers/>
            </CellDivision>
            <CellDeath name="Die if more than 6 neighbors">
                <Condition>n_neighbors > 6</Condition>
            </CellDeath>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type1="cell" type2="cell" value="-10"/>
        </Interaction>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </ShapeSurface>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <MetropolisKinetics temperature="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </MonteCarloSampler>
    </CPM>
    <CellPopulations>
        <Population size="0" type="cell">
            <Cell id="1">
                <Nodes>250,250,0</Nodes>
            </Cell>
            <!--    <Disabled>
        <InitRectangle mode="random" number-of-cells="5">
            <Dimensions size="size" origin="0.0, 0.0, 0.0"/>
        </InitRectangle>
    </Disabled>
-->
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="50">
            <Plot>
                <Cells value="n_neighbors"/>
                <!--    <Disabled>
        <CellLabels value="n_neighbors"/>
    </Disabled>
-->
            </Plot>
            <Terminal name="png"/>
        </Gnuplotter>
    </Analysis>
</MorpheusModel>
```

## CellSorting_2D

```xml
<MorpheusModel version="3">
    <Description>
        <Title>Example-CellSorting-2D</Title>
        <Details>Reference:
Graner and Glazier, Simulation of biological cell sorting using a two-dimensional extended Potts model, Phys. Rev. Lett. 69, 2013–2016 (1992) </Details>
    </Description>
    <Global>
        <Variable symbol="boundary" value="0.0" name="Boundary length of CT1 with other cell types"/>
        <Constant symbol="b" value="0.0"/>
        <Constant symbol="b2" value="0.0"/>
    </Global>
    <Space>
        <SpaceSymbol symbol="l"/>
        <Lattice class="square">
            <Size symbol="size" value="200, 200, 0"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2.5e4"/>
        <!--    <Disabled>
        <SaveInterval value="5e3"/>
    </Disabled>
-->
        <RandomSeed value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="ct1">
            <VolumeConstraint target="200" strength="1"/>
            <NeighborhoodReporter>
                <Input scaling="length" value="cell.type == celltype.ct2.id"/>
                <Output symbol-ref="boundary" mapping="sum"/>
            </NeighborhoodReporter>
            <Property symbol="b" value="0"/>
            <NeighborhoodReporter>
                <Input scaling="cell" value="cell.type == celltype.ct2.id"/>
                <Output symbol-ref="b" mapping="sum"/>
            </NeighborhoodReporter>
            <NeighborhoodReporter>
                <Input scaling="length" value="cell.type == celltype.ct2.id"/>
                <Output symbol-ref="b2" mapping="sum"/>
            </NeighborhoodReporter>
            <Property symbol="b2" value="0" name="Interface with ct2"/>
        </CellType>
        <CellType class="biological" name="ct2">
            <VolumeConstraint target="200" strength="1"/>
            <Property symbol="b" value="0"/>
            <NeighborhoodReporter>
                <Input scaling="cell" value="cell.type == celltype.ct1.id"/>
                <Output symbol-ref="b" mapping="sum"/>
            </NeighborhoodReporter>
            <Property symbol="b2" value="0" name="Interface with ct1"/>
            <NeighborhoodReporter>
                <Input scaling="length" value="cell.type == celltype.ct1.id"/>
                <Output symbol-ref="b2" mapping="sum"/>
            </NeighborhoodReporter>
        </CellType>
        <CellType class="medium" name="medium"/>
    </CellTypes>
    <CPM>
        <Interaction default="0.0">
            <Contact type1="ct1" type2="medium" value="12"/>
            <Contact type1="ct2" type2="medium" value="6"/>
            <Contact type1="ct1" type2="ct1" value="6"/>
            <Contact type1="ct2" type2="ct2" value="6"/>
            <Contact type1="ct1" type2="ct2" value="16"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="2"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>6</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="ct1">
            <InitCircle mode="random" number-of-cells="50">
                <Dimensions radius="size.x/3" center="size.x/2, size.y/2, 0"/>
            </InitCircle>
        </Population>
        <Population size="0" type="ct2">
            <InitCircle mode="random" number-of-cells="50">
                <Dimensions radius="size.x/3" center="size.x/2, size.y/2, 0"/>
            </InitCircle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells flooding="true" value="cell.type"/>
            </Plot>
            <Plot>
                <Cells flooding="true" value="b">
                    <ColorMap>
                        <Color value="2" color="red"/>
                        <Color value="1" color="yellow"/>
                        <Color value="0" color="white"/>
                    </ColorMap>
                </Cells>
                <CellLabels precision="0" fontsize="10" value="b"/>
            </Plot>
            <Plot>
                <Cells per-frame-range="true" value="b2">
                    <ColorMap>
                        <Color value="2" color="red"/>
                        <Color value="1" color="yellow"/>
                        <Color value="0" color="white"/>
                    </ColorMap>
                </Cells>
                <CellLabels precision="0" fontsize="10" value="b2"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="10.0">
            <Input>
                <Symbol symbol-ref="boundary"/>
                <Symbol symbol-ref="b"/>
                <Symbol symbol-ref="b2"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot time-step="500">
                    <Style style="linespoints"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="boundary"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
    </Analysis>
</MorpheusModel>
```

## CellSorting_3D

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-CellSorting-3D</Title>
        <Details>Reference:
Graner and Glazier, Simulation of biological cell sorting using a two-dimensional extended Potts model, Phys. Rev. Lett. 69, 2013–2016 (1992) </Details>
    </Description>
    <Global>
        <Variable value="0.0" symbol="boundary" name="Boundary length of CT1 with other cell types"/>
        <Constant value="0.0" symbol="b"/>
        <Constant value="0.0" symbol="b2"/>
    </Global>
    <Space>
        <SpaceSymbol symbol="l"/>
        <Lattice class="cubic">
            <Size value="100, 100, 100" symbol="size"/>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="25000"/>
        <!--    <Disabled>
        <SaveInterval value="5e3"/>
    </Disabled>
-->
        <RandomSeed value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="medium" name="medium"/>
        <CellType class="biological" name="ct1">
            <VolumeConstraint strength="1" target="1000"/>
            <NeighborhoodReporter>
                <Input value="cell.type == celltype.ct2.id" scaling="length"/>
                <Output symbol-ref="boundary" mapping="sum"/>
            </NeighborhoodReporter>
            <Property value="0" symbol="b"/>
            <NeighborhoodReporter>
                <Input value="cell.type == celltype.ct2.id" scaling="cell"/>
                <Output symbol-ref="b" mapping="sum"/>
            </NeighborhoodReporter>
            <NeighborhoodReporter>
                <Input value="cell.type == celltype.ct2.id" scaling="length"/>
                <Output symbol-ref="b2" mapping="sum"/>
            </NeighborhoodReporter>
            <Property value="0" symbol="b2" name="Interface with ct2"/>
        </CellType>
        <CellType class="biological" name="ct2">
            <VolumeConstraint strength="1" target="1000"/>
            <Property value="0" symbol="b"/>
            <NeighborhoodReporter>
                <Input value="cell.type == celltype.ct1.id" scaling="cell"/>
                <Output symbol-ref="b" mapping="sum"/>
            </NeighborhoodReporter>
            <Property value="0" symbol="b2" name="Interface with ct1"/>
            <NeighborhoodReporter>
                <Input value="cell.type == celltype.ct1.id" scaling="length"/>
                <Output symbol-ref="b2" mapping="sum"/>
            </NeighborhoodReporter>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0.0">
            <Contact type2="medium" type1="ct1" value="12"/>
            <Contact type2="medium" type1="ct2" value="6"/>
            <Contact type2="ct1" type1="ct1" value="6"/>
            <Contact type2="ct2" type1="ct2" value="6"/>
            <Contact type2="ct2" type1="ct1" value="16"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="2"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>2.5</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="ct1">
            <InitCircle mode="random" number-of-cells="30">
                <Dimensions radius="size.x/5" center="size.x/2, size.y/2, size.z/2"/>
            </InitCircle>
        </Population>
        <Population size="0" type="ct2">
            <InitCircle mode="random" number-of-cells="30">
                <Dimensions radius="size.x/5" center="size.x/2, size.y/2, size.z/2"/>
            </InitCircle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" decorate="false">
            <Terminal name="png"/>
            <Plot slice="50">
                <Cells flooding="true" value="cell.type">
                    <ColorMap>
                        <Color value="2" color="green"/>
                        <Color value="1" color="red"/>
                    </ColorMap>
                </Cells>
            </Plot>
            <Plot slice="50">
                <Cells flooding="true" value="b">
                    <ColorMap>
                        <Color value="2" color="red"/>
                        <Color value="1" color="yellow"/>
                        <Color value="0" color="white"/>
                    </ColorMap>
                </Cells>
                <CellLabels precision="0" value="b" fontsize="10"/>
            </Plot>
            <Plot slice="50">
                <Cells per-frame-range="true" value="b2">
                    <ColorMap>
                        <Color value="2" color="red"/>
                        <Color value="1" color="yellow"/>
                        <Color value="0" color="white"/>
                    </ColorMap>
                </Cells>
                <CellLabels precision="0" value="b2" fontsize="10"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="10.0">
            <Input>
                <Symbol symbol-ref="boundary"/>
                <Symbol symbol-ref="b"/>
                <Symbol symbol-ref="b2"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot time-step="500">
                    <Style style="linespoints"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="boundary"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <TiffPlotter compression="false" time-step="50" OME-header="true" format="16bit" timelapse="true">
            <Channel exclude-medium="true" symbol-ref="cell.id"/>
            <Channel exclude-medium="true" symbol-ref="cell.type"/>
        </TiffPlotter>
        <ModelGraph reduced="true" include-tags="#untagged" format="svg"/>
    </Analysis>
</MorpheusModel>
```

## ConvergentExtension

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-Convergence-Extension</Title>
        <Details>Illustrates the plugins MembraneProperty and HomophilicAdhesion
        
        - each cell is polarized through a pattern of concentration c (e.g. of adhesion molecules) along its surface as defined by the plugin MembraneProperty under CellTypes and visualised as black (low c) to yellow (high c) coloration of cell membranes in the plots

        - here the pattern c is predefined as function of direction (angle m.phi of the MembraneLattice defined as m under Space) while PDE-dynamics for c along m on the deforming cell surface is also supported by Morpheus

        - HomophilicAdhesion as Interaction under CPM favors longer contacts between neighboring cells exactly where both adjacent membranes have high values of c, i.e. adhesion is polarised downstream of c
        
        - as emergent behavior, the rectangular tissue gets narrower and higher        
        </Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="square">
            <Size value="500,500,0" symbol="size"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
        <MembraneLattice>
            <Resolution value="20" symbol="memsize"/>
            <SpaceSymbol symbol="m"/>
        </MembraneLattice>
        <SpaceSymbol symbol="l"/>
    </Space>
    <Time>
        <TimeSymbol symbol="TIME"/>
        <StartTime value="0"/>
        <StopTime value="40000"/>
        <!--    <Disabled>
        <RandomSeed value="4"/>
    </Disabled>
-->
        <!--    <Disabled>
        <SaveInterval value="100"/>
    </Disabled>
-->
    </Time>
    <CellTypes>
        <CellType class="biological" name="ct1">
            <PropertyVector value="0.0, 0.0, 0.0" symbol="d"/>
            <VolumeConstraint strength="1" target="2750"/>
            <SurfaceConstraint strength="5" target="1" mode="aspherity"/>
            <MembraneProperty value="sin( (m.phi - 0.75*pi) * 2 ) + 1.0" symbol="c">
                <Diffusion rate="0.0"/>
            </MembraneProperty>
            <Property value="0.0" symbol="pos"/>
            <PersistentMotion strength="1" decay-time="10"/>
        </CellType>
        <CellType class="medium" name="medium">
            <Constant value="0.0" symbol="c"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type2="medium" value="500" type1="ct1"/>
            <Contact type2="ct1" value="0" type1="ct1">
                <HomophilicAdhesion strength="-500" adhesive="c"/>
            </Contact>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="250"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>2</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="ct1" size="0">
            <InitProperty symbol-ref="pos">
                <Expression>rint(cell.center.x / 50)</Expression>
            </InitProperty>
            <InitCellObjects mode="distance">
                <Arrangement displacements="64,80,0" repetitions="6,4,0">
                    <Sphere radius="32" center="82,82,0"/>
                </Arrangement>
                <Arrangement displacements="64,80,0" repetitions="6,4,0">
                    <Sphere radius="32" center="114,122,0"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
        <BoundaryValue value="medium" boundary="x"/>
        <BoundaryValue value="medium" boundary="-x"/>
        <BoundaryValue value="medium" boundary="y"/>
        <BoundaryValue value="medium" boundary="-y"/>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="500" decorate="false">
            <Terminal size="1000,1000,0" name="png"/>
            <Plot>
                <Cells value="c"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="250">
            <Input>
                <Symbol symbol-ref="cell.center.x"/>
                <Symbol symbol-ref="cell.center.y"/>
            </Input>
            <Output>
                <TextOutput file-separation="cell"/>
            </Output>
            <Plots>
                <Plot time-step="2500">
                    <Style style="lines" point-size="0.5"/>
                    <Terminal terminal="png"/>
                    <X-axis maximum="size.x" minimum="0">
                        <Symbol symbol-ref="cell.center.x"/>
                    </X-axis>
                    <Y-axis maximum="size.y" minimum="0">
                        <Symbol symbol-ref="cell.center.y"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="cell.id"/>
                    </Color-bar>
                    <!--    <Disabled>
        <Color-bar>
            <Symbol symbol-ref="TIME"/>
        </Color-bar>
    </Disabled>
-->
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## Crypt

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="3">
    <Description>
        <Title>Example-Crypt</Title>
        <Details>Illustrative model of stem cells in intestinal crypt

Shows the following features of Morpheus:

- Asymmetric cell division (Proliferation)

- Conditionally change cell type (ChangeCellType)

- Loading simulation domain from image (Lattice/Domain)</Details>
    </Description>
    <Global>
        <Variable symbol="w_d" value="3000" name="wait time division"/>
        <Variable symbol="num_A" value="0.0" name="Clone A"/>
        <Variable symbol="num_B" value="0.0" name="Clone B"/>
        <Variable symbol="num_C" value="0.0" name="Clone C"/>
        <Variable symbol="num_D" value="0.0" name="Clone D"/>
        <Variable symbol="num_E" value="0.0" name="Clone E"/>
        <Constant symbol="s" value="0.0"/>
        <Constant symbol="clone" value="0.0"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size symbol="size" value="600 600 0"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <Domain boundary-type="noflux">
                <Image path="assets/crypt-tissue-layout.tif"/>
            </Domain>
        </Lattice>
        <SpaceSymbol symbol="l"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="50000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="stem_cells">
            <Property symbol="clone" value="0.0"/>
            <Property symbol="t_d" value="0.0" name="time of division"/>
            <Property symbol="s" value="1" name="stemness"/>
            <VolumeConstraint target="800" strength="1"/>
            <SurfaceConstraint target="1" mode="aspherity" strength="1"/>
            <ChangeCellType newCellType="TA_cells">
                <Condition>s==0</Condition>
                <Triggers/>
            </ChangeCellType>
            <DirectedMotion direction="0, -1,  0" strength="0.5"/>
            <CellDivision daughterID="daughter" division-plane="random">
                <Condition>time > t_d</Condition>
                <Triggers>
                    <Rule symbol-ref="s">
                        <Expression>if( daughter == 1, 1, 0 )</Expression>
                    </Rule>
                    <Rule symbol-ref="t_d">
                        <Expression>time + rand_norm(w_d,200)</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
        </CellType>
        <CellType class="biological" name="TA_cells">
            <Property symbol="clone" value="0.0"/>
            <Property symbol="t_d" value="0" name="time of division"/>
            <Property symbol="d" value="0" name="divisions"/>
            <VolumeConstraint target="600 " strength="1"/>
            <SurfaceConstraint target="0.9" mode="aspherity" strength="1"/>
            <CellDivision daughterID="daughter" division-plane="random">
                <Condition>time > t_d</Condition>
                <Triggers>
                    <Rule symbol-ref="d">
                        <Expression>d+0.5</Expression>
                    </Rule>
                    <Rule symbol-ref="t_d">
                        <Expression>time + rand_norm(w_d,500)</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
            <CellDeath>
                <Condition>if( cell.center.y > size.y - 20, 1, 0)</Condition>
            </CellDeath>
            <Mapper name="Count Clone A">
                <Input value="clone==1"/>
                <Output symbol-ref="num_A" mapping="sum"/>
            </Mapper>
            <Mapper name="Count Clone B">
                <Input value=" clone==2"/>
                <Output symbol-ref="num_B" mapping="sum"/>
            </Mapper>
            <Mapper name="Count Clone C">
                <Input value="clone==3"/>
                <Output symbol-ref="num_C" mapping="sum"/>
            </Mapper>
            <Mapper name="Count Clone D">
                <Input value="clone==4"/>
                <Output symbol-ref="num_D" mapping="sum"/>
            </Mapper>
            <Mapper name="Count Clone E">
                <Input value="clone==5"/>
                <Output symbol-ref="num_E" mapping="sum"/>
            </Mapper>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact type1="stem_cells" type2="stem_cells" value="-10"/>
            <Contact type1="stem_cells" type2="TA_cells" value="10"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1.0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="3" yield="0.1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>2.5</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="0" type="stem_cells">
            <InitRectangle mode="regular" number-of-cells="5">
                <Dimensions size="100,30,0" origin="250.0, 75.0, 0.0"/>
            </InitRectangle>
            <InitProperty symbol-ref="clone">
                <Expression>cell.id</Expression>
            </InitProperty>
            <InitProperty symbol-ref="t_d">
                <Expression>rand_uni(0,w_d)</Expression>
            </InitProperty>
        </Population>
        <Population size="0" type="TA_cells">
            <InitRectangle mode="regular" number-of-cells="500">
                <Dimensions size="600, 490, 0" origin="0,80, 0"/>
            </InitRectangle>
            <InitProperty symbol-ref="t_d">
                <Expression>rand_uni(0,w_d)</Expression>
            </InitProperty>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="250" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="clone">
                    <ColorMap>
                        <Color value="20" color="gold"/>
                        <Color value="19" color="dark-pink"/>
                        <Color value="18" color="dark-khaki"/>
                        <Color value="17" color="dark-goldenrod"/>
                        <Color value="16" color="cyan"/>
                        <Color value="15" color="coral"/>
                        <Color value="14" color="chartreuse"/>
                        <Color value="13" color="brown4"/>
                        <Color value="12" color="bisque"/>
                        <Color value="11" color="beige"/>
                        <Color value="10" color="light-red"/>
                        <Color value="9" color="light-green"/>
                        <Color value="8" color="light-blue"/>
                        <Color value="7" color="gray"/>
                        <Color value="6" color="black"/>
                        <Color value="5" color="yellow"/>
                        <Color value="4" color="blue"/>
                        <Color value="3" color="green"/>
                        <Color value="2" color="red"/>
                    </ColorMap>
                </Cells>
            </Plot>
        </Gnuplotter>
        <Logger time-step="100">
            <Input>
                <Symbol symbol-ref="num_A"/>
                <Symbol symbol-ref="num_B"/>
                <Symbol symbol-ref="num_C"/>
                <Symbol symbol-ref="num_D"/>
                <Symbol symbol-ref="num_E"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot title="Clone numbers" time-step="5000">
                    <Style point-size="1" grid="true" style="linespoints" line-width="3.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="num_A"/>
                        <Symbol symbol-ref="num_B"/>
                        <Symbol symbol-ref="num_C"/>
                        <Symbol symbol-ref="num_D"/>
                        <Symbol symbol-ref="num_E"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph format="svg" reduced="true" />
    </Analysis>
</MorpheusModel>
```

## Persistence_2D

```xml
<MorpheusModel version="3">
    <Description>
        <Title>Example-Persistence</Title>
        <Details>Illustrates the Plugin PersistentMotion and shows

        - 400 cells confined to a circular domain (defined in Space) and forced to move with persistence
        
        - rectangular obstacle without dynamics since FreezeMotion is set of this cell type

        - alignment of motion directions emerges from the random initial state as a collective effect
        </Details>
    </Description>
    <Global>
        <VariableVector symbol="d" value="0.0, 0.0, 0.0" name="Moving direction"/>
        <Constant symbol="density" value="0.012"/>
    </Global>
    <Space>
        <Lattice class="square">
            <Size symbol="size" value="200, 200, 0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <Domain boundary-type="constant">
                <Circle diameter="200"/>
            </Domain>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <TimeSymbol symbol="time"/>
        <StartTime value="0"/>
        <StopTime value="5000"/>
        <RandomSeed value="4"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="obstacle">
            <FreezeMotion>
                <Condition>1</Condition>
            </FreezeMotion>
        </CellType>
        <CellType class="biological" name="ct1">
            <PropertyVector symbol="d" value="0.0, 0.0, 0.0" name="Moving direction"/>
            <Property symbol="s" value="5"/>
            <VolumeConstraint target="100" strength="1"/>
            <SurfaceConstraint target="0.9" mode="aspherity" strength="1"/>
            <PersistentMotion protrusion="true" decay-time="50" strength="s"/>
            <MotilityReporter time-step="50">
                <Velocity symbol-ref="d"/>
            </MotilityReporter>
        </CellType>
        <CellType class="medium" name="medium"/>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type1="ct1" type2="medium" value="16"/>
            <Contact type1="ct1" type2="ct1" value="1"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="10"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>3</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population size="1" type="obstacle">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Box size="20,30,0" origin="130,100,0"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
        <Population size="0" type="ct1">
            <InitCircle mode="regular" number-of-cells="400">
                <Dimensions radius="100" center="100, 100, 0"/>
            </InitCircle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100">
            <Terminal size="1000 600 0" name="png"/>
            <Plot>
                <Cells value="cell.id"/>
                <!--    <Disabled>
        <CellArrows style="1" orientation="3 * d / d.abs"/>
    </Disabled>
-->
            </Plot>
            <Plot>
                <Cells value="d.phi" min="0.0" max="6.28">
                    <ColorMap>
                        <Color value="6.28" color="red"/>
                        <Color value="3.14" color="blue"/>
                        <Color value="0.0" color="red"/>
                    </ColorMap>
                </Cells>
                <CellArrows style="1" orientation="3 * d / d.abs"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="10">
            <Input>
                <Symbol symbol-ref="cell.center.x"/>
                <Symbol symbol-ref="cell.center.y"/>
            </Input>
            <Output>
                <TextOutput file-separation="cell"/>
            </Output>
            <Plots>
                <Plot time-step="50">
                    <Style style="lines" line-width="2.0"/>
                    <Terminal terminal="png"/>
                    <X-axis minimum="0.0" maximum="size.x">
                        <Symbol symbol-ref="cell.center.x"/>
                    </X-axis>
                    <Y-axis minimum="0.0" maximum="size.y">
                        <Symbol symbol-ref="cell.center.y"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="time"/>
                    </Color-bar>
                    <Range>
                        <Time mode="history" history="50"/>
                    </Range>
                </Plot>
            </Plots>
        </Logger>
    </Analysis>
</MorpheusModel>
```

## PigmentCells

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="1">
    <Description>
        <Details></Details>
        <Title></Title>
    </Description>
    <Global>
        <Constant symbol="yellow" value="0"/>
        <Constant symbol="black" value="0"/>
        <ConstantVector symbol="direction" value="0.0, 0.0, 0.0"/>
        <Field symbol="c" value="0" name="chemoattractant">
            <Diffusion rate="20"/>
        </Field>
        <System solver="runge-kutta" time-step="2">
            <DiffEqn symbol-ref="c">
                <Expression>black - c</Expression>
            </DiffEqn>
        </System>
        <Field symbol="act" value="0" name="activity">
            <Diffusion rate="0"/>
        </Field>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="300, 300, 0"/>
            <!--    <Disabled>
        <BoundaryConditions>
            <Condition boundary="x" type="noflux"/>
            <Condition boundary="y" type="noflux"/>
            <Condition boundary="-x" type="noflux"/>
            <Condition boundary="-y" type="noflux"/>
        </BoundaryConditions>
    </Disabled>
-->
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
        <MembraneLattice>
            <Resolution value="40"/>
        </MembraneLattice>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="1000"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="yellow">
            <VolumeConstraint target="500" strength="1"/>
            <SurfaceConstraint target="1.5" strength="1"/>
            <Property symbol="yellow" value="1"/>
            <PropertyVector symbol="direction" value="0,0,0"/>
            <CellReporter name="sense chemoattractant">
                <Input value="c"/>
                <Polarity symbol-ref="direction"/>
            </CellReporter>
            <DirectedMotion direction="direction" strength="0.25" name="&quot;whole-cell chemotaxis&quot;"/>
        </CellType>
        <CellType class="biological" name="black">
            <Property symbol="black" value="1"/>
            <VolumeConstraint target="2500" strength="1"/>
            <SurfaceConstraint target="1" strength="1"/>
            <MembraneProperty symbol="contact" value="0">
                <Diffusion rate="0.0"/>
            </MembraneProperty>
            <NeighborhoodReporter name="record contact to yellow cell">
                <Input scaling="length" value="yellow"/>
                <Output symbol-ref="contact" mapping="average"/>
            </NeighborhoodReporter>
            <CellReporter name="compute vector to contact">
                <Input value="contact"/>
                <Polarity symbol-ref="direction"/>
            </CellReporter>
            <PropertyVector symbol="direction" value="0,0,0"/>
            <DirectedMotion direction="-direction" strength="1" name="move away from contact"/>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0.0"/>
        <MCSDuration value="1"/>
        <MetropolisKinetics temperature="1" stepper="edgelist">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </MetropolisKinetics>
    </CPM>
    <CellPopulations>
        <Population size="0" type="yellow">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Object>
                        <Sphere radius="15" center="50,150,0"/>
                    </Object>
                </Arrangement>
            </InitCellObjects>
        </Population>
        <Population size="0" type="black">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Object>
                        <Sphere radius="30" center="160,150,0"/>
                    </Object>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter clean="true" time-step="25">
            <Plot>
                <Cells value="cell.id">
                    <!--    <Disabled>
        <ColorMap>
            <Color value="2" color="black"/>
            <Color value="0" color="yellow"/>
        </ColorMap>
    </Disabled>
-->
                </Cells>
                <!--    <Disabled>
        <CellArrows orientation="-direction*100"/>
    </Disabled>
-->
                <Field resolution="50" symbol-ref="c"/>
            </Plot>
            <!--    <Disabled>
        <Plot>
            <Cells value="contact">
                <Disabled>
                    <ColorMap>
                        <Color value="1" color="black"/>
                        <Color value="0" color="yellow"/>
                    </ColorMap>
                </Disabled>
            </Cells>
            <CellLabels symbol-ref="cell.type" fontcolor="red"/>
            <Disabled>
                <Field resolution="50" symbol-ref="act"/>
            </Disabled>
        </Plot>
    </Disabled>
-->
            <Terminal opacity="0.75" name="png"/>
        </Gnuplotter>
    </Analysis>
</MorpheusModel>
```

## Proliferation_2D

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-Proliferation2D</Title>
        <Details>Illustrates Plugin CellDivision under CellTypes
        
        - here, any cell can divide symmetrically with probability p and daughters then increase their counter d of dividion rounds by 1 (plotted as number inside each cell)

        - to highlight recent division events, both daughters are labeled red for some time (controled by a counter c as CellProperty)
        
        </Details>
    </Description>
    <Global>
        <Variable symbol="c" value="0.0"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="500, 500, 0"/>
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
        <StopTime symbol="stoptime" value="4e4"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType name="cells" class="biological">
            <Property symbol="p" value="5e-5" name="proliferation rate"/>
            <Property symbol="d" value="0" name="divisions"/>
            <Property symbol="c" value="0" name="color"/>
            <VolumeConstraint strength="1" target="500"/>
            <SurfaceConstraint mode="aspherity" strength="1" target="0.9"/>
            <System solver="Euler [fixed, O(1)]" time-step="1.0">
                <Rule symbol-ref="c">
                    <Expression>if( c > 0, c-1, 0)</Expression>
                </Rule>
            </System>
            <CellDivision division-plane="random">
                <Condition>rand_uni(0,1) &lt; p</Condition>
                <Triggers>
                    <Rule symbol-ref="d">
                        <Expression>d+1</Expression>
                    </Rule>
                    <Rule symbol-ref="c" name="color after division">
                        <Expression>1000</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact value="-4" type2="cells" type1="cells"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1.0"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="3" yield="0.1"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="cells" size="1">
            <InitCircle mode="regular" number-of-cells="20">
                <Dimensions radius="35" center="250, 250, 0"/>
            </InitCircle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter decorate="false" time-step="1000">
            <Terminal name="png"/>
            <Plot>
                <Cells value="c" min="0.0" max="1">
                    <ColorMap>
                        <Color value="1" color="red"/>
                        <Color value="0.0" color="green"/>
                    </ColorMap>
                </Cells>
                <CellLabels value="d" fontsize="8"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="100">
            <Input>
                <Symbol symbol-ref="celltype.cells.size"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot log-commands="true" time-step="10000">
                    <Style grid="true" style="linespoints" point-size="0.5"/>
                    <Terminal terminal="png"/>
                    <X-axis minimum="0" maximum="stoptime">
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis minimum="0" maximum="100">
                        <Symbol symbol-ref="celltype.cells.size"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph reduced="false" include-tags="#untagged" format="svg"/>
    </Analysis>
</MorpheusModel>
```

## Proliferation_3D

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-Proliferation3D</Title>
        <Details>Illustrates size-dependent cell division and plotting 2D slices of 3D configurations
        
        - Upon cell division, two daughters are initialised each with its half the mother's occupied volume, then CPM dynamics lets each daughter grow to the target volume are the mother had.  
        
        - A condition for CellDivision is used that combines (logic and) a threshold (actual cell size > threshold) with a probability to divide.
        </Details>
    </Description>
    <Global/>
    <Space>
        <Lattice class="cubic">
            <Size symbol="size" value="100, 100, 100"/>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
                <Condition type="noflux" boundary="z"/>
                <Condition type="noflux" boundary="-z"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </Lattice>
        <MembraneLattice>
            <Resolution symbol="memsize" value="20"/>
            <SpaceSymbol symbol="m"/>
        </MembraneLattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="2500"/>
        <TimeSymbol symbol="time"/>
        <RandomSeed value="1456688742"/>
    </Time>
    <CellTypes>
        <CellType class="medium" name="medium"/>
        <CellType class="medium" name="matrix"/>
        <CellType class="biological" name="cell">
            <Property symbol="Vt" value="500" name="Target Volume"/>
            <Property symbol="divisions" value="0"/>
            <VolumeConstraint target="Vt" strength="1.0"/>
            <SurfaceConstraint target="1.0" strength="1.0" mode="aspherity"/>
            <CellDivision division-plane="major">
                <Condition>rand_uni(0,1) &lt; 0.0025 and cell.volume > Vt*0.9</Condition>
                <Triggers>
                    <Rule symbol-ref="divisions">
                        <Expression>divisions + 0.5</Expression>
                    </Rule>
                </Triggers>
            </CellDivision>
            <MembraneProperty symbol="c" value="1">
                <Diffusion rate="0.0"/>
            </MembraneProperty>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction default="0">
            <Contact type1="cell" type2="cell" value="-6"/>
            <Contact type1="cell" type2="medium" value="0"/>
            <Contact type1="cell" type2="matrix" value="-2"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="0.5"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>2.5</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="cell" size="0">
            <InitCellObjects mode="distance">
                <Arrangement displacements="1, 1, 1" repetitions="1, 1, 1">
                    <Sphere radius="5" center="50,50,50"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
        <BoundaryValue boundary="x" value="matrix"/>
        <BoundaryValue boundary="-x" value="matrix"/>
        <BoundaryValue boundary="y" value="matrix"/>
        <BoundaryValue boundary="-y" value="matrix"/>
        <BoundaryValue boundary="z" value="matrix"/>
        <BoundaryValue boundary="-z" value="matrix"/>
    </CellPopulations>
    <Analysis>
        <TiffPlotter time-step="100" format="8bit" compression="false" timelapse="true" OME-header="true">
            <Channel exclude-medium="true" symbol-ref="cell.id"/>
            <Channel exclude-medium="true" celltype="cell" symbol-ref="c" outline="true"/>
        </TiffPlotter>
        <Gnuplotter time-step="100" decorate="true">
            <Plot slice="50">
                <Cells value="cell.id"/>
            </Plot>
            <Terminal name="png"/>
        </Gnuplotter>
        <Logger time-step="100">
            <Input>
                <Symbol symbol-ref="celltype.cell.size"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot time-step="500">
                    <Style style="linespoints"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="celltype.cell.size"/>
                    </Y-axis>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph format="svg" include-tags="#untagged" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## Protrusion

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="2">
    <Description>
        <Title>Example-Protrusion</Title>
        <Details>Model for cell protrusions using the Act model. 

The Act model defines a local positive feedback mechanism, insprired by actin dynamics, that promotes protrusions in recently active areas.

Reference:
Ioana Niculescu, Johannes Textor, Rob J. de Boer, Crawling and Gliding: A Computational Model for Shape-Driven Cell Migration, PLoS Comp Biol, 2015.
http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004280</Details>
    </Description>
    <Global>
        <Field symbol="act" value="0" name="actin activity">
            <Diffusion rate="0"/>
        </Field>
        <!--    <Disabled>
        <System solver="euler" time-step="1.0">
            <Rule symbol-ref="act">
                <Expression>act</Expression>
            </Rule>
        </System>
    </Disabled>
-->
    </Global>
    <Space>
        <Lattice class="cubic">
            <Size symbol="size" value="200, 200, 200"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
                <Condition boundary="y" type="periodic"/>
            </BoundaryConditions>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="5000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="amoeba">
            <VolumeConstraint target="25000" strength="50"/>
            <SurfaceConstraint target="0.8" strength="5"/>
            <Protrusion field="act" maximum="80" strength="80"/>
            <!--    <Disabled>
        <ConnectivityConstraint/>
    </Disabled>
-->
        </CellType>
        <CellType class="medium" name="medium"/>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type1="amoeba" type2="medium" value="140"/>
            <Contact type1="medium" type2="medium" value="0"/>
        </Interaction>
        <MCSDuration value="1"/>
        <MetropolisKinetics temperature="20" stepper="edgelist">
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </MetropolisKinetics>
    </CPM>
    <CellPopulations>
        <Population size="0" type="amoeba">
            <InitCellObjects mode="distance">
                <Arrangement repetitions="1, 1, 1" displacements="1, 1, 1">
                    <Object>
                        <Sphere radius="10" center="100,100,100"/>
                    </Object>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" interpolation="false" decorate="false">
            <Terminal opacity="0.2" name="png"/>
            <Plot>
                <Cells value="cell.id" slice="100">
                    <!--    <Disabled>
        <ColorMap>
            <Color value="1" color="gray20"/>
            <Color value="0.0" color="gray50"/>
        </ColorMap>
    </Disabled>
-->
                </Cells>
                <Field symbol-ref="act" slice="100"/>
            </Plot>
        </Gnuplotter>
        <TiffPlotter timelapse="true" format="8bit" OME-header="true" compression="false" time-step="100">
            <Channel symbol-ref="cell.id" exclude-medium="true"/>
            <Channel symbol-ref="act"/>
        </TiffPlotter>
    </Analysis>
</MorpheusModel>
```

## Protrusion_2D

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-Protrusion</Title>
        <Details>Model for cell protrusions using the Act model. 

The Act model defines a local positive feedback mechanism, insprired by actin dynamics, that promotes protrusions in recently active areas.

Reference:
Ioana Niculescu, Johannes Textor, Rob J. de Boer, Crawling and Gliding: A Computational Model for Shape-Driven Cell Migration, PLoS Comp Biol, 2015.
http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004280</Details>
    </Description>
    <Global>
        <Field symbol="act" value="0" name="actin activity">
            <Diffusion rate="0"/>
        </Field>
        <!--    <Disabled>
        <System time-step="1.0" solver="Euler [fixed, O(1)]">
            <Rule symbol-ref="act">
                <Expression>act</Expression>
            </Rule>
        </System>
    </Disabled>
-->
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="200, 200, 0"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="15000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="amoeba">
            <VolumeConstraint target="2500" strength="50"/>
            <SurfaceConstraint target="1" strength="5" mode="aspherity"/>
            <Protrusion field="act" strength="80" maximum="200"/>
            <ConnectivityConstraint/>
        </CellType>
        <CellType class="medium" name="medium"/>
        <CellType class="biological" name="obstacle">
            <FreezeMotion>
                <Condition>1</Condition>
            </FreezeMotion>
        </CellType>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type1="amoeba" type2="medium" value="140"/>
            <Contact type1="medium" type2="medium" value="0"/>
            <Contact type1="amoeba" type2="obstacle" value="140"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="20"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="amoeba" size="0">
            <InitCellObjects mode="distance">
                <Arrangement displacements="1, 1, 1" repetitions="1, 1, 1">
                    <Sphere radius="25" center="100,100,0"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
        <Population type="obstacle" size="1">
            <InitCellObjects mode="distance">
                <Arrangement displacements="100, 1, 1" repetitions="2, 1, 1">
                    <Sphere radius="10" center="50,100,0"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="250" decorate="false">
            <Terminal name="png"/>
            <Plot>
                <Cells value="cell.id" opacity="0.2">
                    <!--    <Disabled>
        <ColorMap>
            <Color color="gray20" value="1"/>
            <Color color="gray50" value="0.0"/>
        </ColorMap>
    </Disabled>
-->
                </Cells>
                <Field symbol-ref="act"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="10">
            <Input>
                <Symbol symbol-ref="cell.center.x"/>
                <Symbol symbol-ref="cell.center.y"/>
            </Input>
            <Output>
                <TextOutput file-separation="cell"/>
            </Output>
            <Plots>
                <Plot time-step="-1">
                    <Style line-width="2.0" style="lines"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="cell.center.x"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="cell.center.y"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="time"/>
                    </Color-bar>
                    <!--    <Disabled>
        <Range>
            <Time mode="history"/>
        </Range>
    </Disabled>
-->
                </Plot>
            </Plots>
            <Restriction>
                <Celltype celltype="amoeba"/>
            </Restriction>
        </Logger>
        <ModelGraph format="svg" include-tags="#untagged" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## Protrusion_3D

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-Protrusion</Title>
        <Details>Model for cell protrusions using the Act model. 

The Act model defines a local positive feedback mechanism, insprired by actin dynamics, that promotes protrusions in recently active areas.

Reference:
Ioana Niculescu, Johannes Textor, Rob J. de Boer, Crawling and Gliding: A Computational Model for Shape-Driven Cell Migration, PLoS Comp Biol, 2015.
http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004280</Details>
    </Description>
    <Global>
        <Field symbol="act" value="0" name="actin activity">
            <Diffusion rate="0"/>
        </Field>
    </Global>
    <Space>
        <Lattice class="cubic">
            <Size symbol="size" value="200, 200, 200"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="5000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="amoeba">
            <VolumeConstraint target="25000" strength="50"/>
            <SurfaceConstraint target="1.5" strength="5" mode="aspherity"/>
            <Protrusion field="act" strength="80" maximum="150"/>
            <!--    <Disabled>
        <ConnectivityConstraint/>
    </Disabled>
-->
        </CellType>
        <CellType class="medium" name="medium"/>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type1="amoeba" type2="medium" value="140"/>
            <Contact type1="medium" type2="medium" value="0"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="20"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="amoeba" size="0">
            <InitCellObjects mode="distance">
                <Arrangement displacements="1, 1, 1" repetitions="1, 1, 1">
                    <Sphere radius="10" center="100,100,100"/>
                </Arrangement>
            </InitCellObjects>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="100" decorate="false">
            <Terminal name="png"/>
            <Plot slice="100">
                <Cells value="cell.id" opacity="0.2">
                    <!--    <Disabled>
        <ColorMap>
            <Color color="gray20" value="1"/>
            <Color color="gray50" value="0.0"/>
        </ColorMap>
    </Disabled>
-->
                </Cells>
                <Field symbol-ref="act"/>
            </Plot>
        </Gnuplotter>
        <TiffPlotter time-step="100" format="guess" compression="false" timelapse="true" OME-header="true">
            <Channel exclude-medium="true" no-outline="true" symbol-ref="cell.id"/>
            <Channel symbol-ref="act"/>
        </TiffPlotter>
        <ModelGraph format="svg" include-tags="#untagged" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## RunAndTumble

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Title>Example-RunAndTumble</Title>
        <Details>Models a Levy walk - a random walk strategy that is superior for searching due to it's high spatial coverage.

Shows how to manipulate PropertyVectors (x,z,y) using the VectorRule. An expression for each of the three coordinates must be given, separated by a comma ",".</Details>
    </Description>
    <Global>
        <Constant symbol="tumble.run_duration" value="0"/>
    </Global>
    <Space>
        <Lattice class="hexagonal">
            <Size symbol="size" value="300, 300, 0"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <BoundaryConditions>
                <Condition type="periodic" boundary="x"/>
                <Condition type="periodic" boundary="y"/>
            </BoundaryConditions>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="10000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <CellTypes>
        <CellType class="biological" name="amoeba">
            <VolumeConstraint target="200" strength="1"/>
            <ConnectivityConstraint/>
            <PropertyVector symbol="move_dir" value="0.0, 0.0, 0.0"/>
            <Property symbol="tumble.run_duration" value="0.0" name="run duration"/>
            <Property symbol="tumble.last" value="0" name="last tumble event"/>
            <Function symbol="tumble.time_left" name="time left">
                <Expression>tumble.last + tumble.run_duration - time</Expression>
            </Function>
            <DirectedMotion direction="move_dir" strength="0.1"/>
            <Event time-step="5" trigger="when true">
                <Condition>time >= tumble.last + tumble.run_duration</Condition>
                <Rule symbol-ref="tumble.last">
                    <Expression>time</Expression>
                </Rule>
                <Rule name="new update time" symbol-ref="tumble.run_duration">
                    <Expression>20 * rand_gamma(0.5, 5)</Expression>
                </Rule>
                <Intermediate symbol="angle" value="rand_uni(0, 2*pi)"/>
                <VectorRule notation="r,φ,θ" symbol-ref="move_dir">
                    <Expression>1, angle, 0</Expression>
                </VectorRule>
            </Event>
            <Event time-step="100">
                <Condition>time == 0</Condition>
                <VectorRule symbol-ref="cell.center.initial">
                    <Expression>cell.center</Expression>
                </VectorRule>
            </Event>
            <PropertyVector symbol="cell.center.initial" value="0.0, 0.0, 0.0"/>
            <PropertyVector symbol="cell.center.relative" value="0.0, 0.0, 0.0"/>
            <VectorEquation symbol-ref="cell.center.relative">
                <Expression>cell.center - cell.center.initial</Expression>
            </VectorEquation>
        </CellType>
        <CellType class="medium" name="medium"/>
    </CellTypes>
    <CPM>
        <Interaction>
            <Contact type1="amoeba" type2="medium" value="4"/>
            <Contact type1="amoeba" type2="amoeba" value="6.0"/>
        </Interaction>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <MetropolisKinetics temperature="0.6"/>
        </MonteCarloSampler>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Distance>2.5</Distance>
            </Neighborhood>
        </ShapeSurface>
    </CPM>
    <CellPopulations>
        <Population type="amoeba" size="1">
            <Cell name="1" id="1">
                <Nodes>50,100,0</Nodes>
            </Cell>
            <Cell name="2" id="2">
                <Nodes>150, 50,0</Nodes>
            </Cell>
            <Cell name="3" id="3">
                <Nodes>100,50,0</Nodes>
            </Cell>
            <Cell name="4" id="4">
                <Nodes>100,100,0</Nodes>
            </Cell>
            <Cell name="5" id="5">
                <Nodes>50, 150,0</Nodes>
            </Cell>
            <Cell name="6" id="6">
                <Nodes>100, 150,0</Nodes>
            </Cell>
            <Cell name="7" id="7">
                <Nodes>150, 100,0</Nodes>
            </Cell>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="200" decorate="true">
            <Terminal name="png"/>
            <Plot>
                <Cells value="cell.id"/>
                <CellArrows orientation="5 * move_dir"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="20">
            <Input>
                <Symbol symbol-ref="cell.center.relative.x"/>
                <Symbol symbol-ref="cell.center.relative.y"/>
            </Input>
            <Output>
                <TextOutput file-separation="cell"/>
            </Output>
            <Plots>
                <Plot time-step="5000">
                    <Style line-width="2.0" style="lines"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="cell.center.relative.x"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="cell.center.relative.y"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="cell.id"/>
                    </Color-bar>
                </Plot>
            </Plots>
            <Restriction/>
        </Logger>
        <ModelGraph format="svg" include-tags="#untagged" reduced="true"/>
    </Analysis>
</MorpheusModel>
```

## Stigmergy_VectorField

```xml
<?xml version='1.0' encoding='UTF-8'?>
<MorpheusModel version="4">
    <Description>
        <Details>Cells move in  a persistent way and modify their einvironment according to their moving direction.
This orientational information is stored in a VectorField, which decays over time.
Cells also tend to follow this orientational information, which can lead to the spontaneous formation of local swirls that continuously self-reenforce.</Details>
        <Title>VectorField-Stigmergy</Title>
    </Description>
    <Space>
        <Lattice class="square">
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
            <Size symbol="size" value="300,300,0"/>
            <!--    <Disabled>
        <BoundaryConditions>
            <Condition type="noflux" boundary="x"/>
            <Condition type="noflux" boundary="y"/>
            <Condition type="noflux" boundary="-x"/>
            <Condition type="noflux" boundary="-y"/>
        </BoundaryConditions>
    </Disabled>
-->
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="5000"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Global>
        <VectorField symbol="v" value="0.0, 0.0, 0.0"/>
        <Constant symbol="cell" value="0.0"/>
        <ConstantVector symbol="velocity" value="0.0, 0.0, 0.0"/>
        <System time-step="1.0" solver="Runge-Kutta [fixed, O(4)]">
            <VectorRule symbol-ref="v">
                <Expression>if(cell, v.x+alpha*velocity.x, v.x-delta*v.x),
if(cell, v.y+alpha*velocity.y, v.y-delta*v.y),
0</Expression>
            </VectorRule>
            <Constant symbol="delta" value="0.002"/>
            <Constant symbol="alpha" value="0.1"/>
        </System>
    </Global>
    <CellTypes>
        <CellType name="cell" class="biological">
            <Property symbol="cell" value="1"/>
            <PropertyVector symbol="velocity" value="0.0, 0.0, 0.0"/>
            <MotilityReporter time-step="1" name="report movement">
                <Velocity symbol-ref="velocity"/>
            </MotilityReporter>
            <VolumeConstraint target="100" strength="1"/>
            <SurfaceConstraint target="1" strength="1" mode="aspherity"/>
            <PersistentMotion decay-time="30" strength="2.0"/>
            <DirectedMotion strength="2" direction="v"/>
        </CellType>
    </CellTypes>
    <CellPopulations>
        <Population type="cell" size="1">
            <InitRectangle random-offset="20" mode="regular" number-of-cells="20">
                <Dimensions origin="size/10" size="9*size/10"/>
            </InitRectangle>
        </Population>
    </CellPopulations>
    <Analysis>
        <Gnuplotter time-step="50" decorate="false">
            <Plot>
                <VectorField style="8" color="black" coarsening="6" value="3*v"/>
                <Cells opacity="0.5" value="cell.id"/>
            </Plot>
            <Terminal name="png"/>
        </Gnuplotter>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
    <CPM>
        <Interaction>
            <Contact type2="cell" type1="cell" value="10"/>
        </Interaction>
        <ShapeSurface scaling="norm">
            <Neighborhood>
                <Order>3</Order>
            </Neighborhood>
        </ShapeSurface>
        <MonteCarloSampler stepper="edgelist">
            <MCSDuration value="1"/>
            <MetropolisKinetics temperature="10"/>
            <Neighborhood>
                <Order>2</Order>
            </Neighborhood>
        </MonteCarloSampler>
    </CPM>
</MorpheusModel>
```
