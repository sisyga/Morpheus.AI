# Partial Differential Equation (PDE) Examples

Reference MorpheusML v4 XML models for pde simulations.

---

## ActivatorInhibitor_1D

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-ActivatorInhibitor1D</Title>
        <Details></Details>
    </Description>
    <Global>
        <Field name="activator" value="rand_norm(0.5,0.1)" symbol="a">
            <Diffusion rate="0.02"/>
        </Field>
        <Field name="inhibitor" value="0.1" symbol="i">
            <Diffusion rate="1"/>
        </Field>
        <System time-step="1" solver="Runge-Kutta [fixed, O(4)]">
            <DiffEqn symbol-ref="a">
                <Expression>(rho*a^2) / i - mu_a * a + rho_a</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="i">
                <Expression>(rho*a^2) - mu_i * i</Expression>
            </DiffEqn>
            <Constant value="0.01" symbol="rho_a"/>
            <Constant value="0.03" symbol="mu_i"/>
            <Constant value="0.02" symbol="mu_a"/>
            <Constant value="0.001" symbol="rho"/>
        </System>
    </Global>
    <Space>
        <Lattice class="linear">
            <Size value="100, 0, 0" symbol="size"/>
            <BoundaryConditions>
                <Condition boundary="x" type="periodic"/>
            </BoundaryConditions>
            <NodeLength value="0.25"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="4000"/>
        <SaveInterval value="0"/>
        <!--    <Disabled>
        <RandomSeed value="1"/>
    </Disabled>
-->
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Logger time-step="25">
            <Input>
                <Symbol symbol-ref="a"/>
                <Symbol symbol-ref="i"/>
            </Input>
            <Output>
                <TextOutput/>
            </Output>
            <Plots>
                <Plot title="space plot" time-step="250">
                    <Style style="lines" line-width="3.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="space.x"/>
                    </X-axis>
                    <Y-axis minimum="0" maximum="3.5">
                        <Symbol symbol-ref="a"/>
                        <Symbol symbol-ref="i"/>
                    </Y-axis>
                    <Range>
                        <Time mode="current"/>
                    </Range>
                </Plot>
                <Plot title="time-space plot" time-step="-1">
                    <Style style="points"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="time"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="space.x"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="a"/>
                    </Color-bar>
                </Plot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## ActivatorInhibitor_2D

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-ActivatorInhibitor-2D</Title>
        <Details></Details>
    </Description>
    <Global>
        <Field name="activator" value="rand_norm(0.5,0.1)" symbol="a">
            <Diffusion rate="0.02"/>
        </Field>
        <Field name="inhibitor" value="0.1" symbol="i">
            <Diffusion rate="1"/>
        </Field>
        <System name="Meinhardt" time-step="5" solver="Runge-Kutta [fixed, O(4)]">
            <Constant value="0.001" symbol="rho"/>
            <Constant value="0.001" symbol="rho_a"/>
            <Constant value="0.03" symbol="mu_i"/>
            <Constant value="0.02" symbol="mu_a"/>
            <Constant value="0.10" symbol="kappa"/>
            <DiffEqn symbol-ref="a">
                <Expression>(rho/i)*((a^2)/(1 + kappa*a^2)) - mu_a * a + rho_a</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="i">
                <Expression>rho*((a^2)/(1+kappa*a^2)) - mu_i *i</Expression>
            </DiffEqn>
        </System>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="150, 150, 0" symbol="size"/>
            <NodeLength value="1"/>
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
        <StopTime value="12500"/>
        <SaveInterval value="0"/>
        <RandomSeed value="2"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Gnuplotter decorate="false" time-step="500">
            <Terminal size="400 400 0" name="png"/>
            <Plot>
                <Field min="0" symbol-ref="a"/>
            </Plot>
        </Gnuplotter>
        <Logger time-step="250">
            <Input>
                <Symbol symbol-ref="a"/>
            </Input>
            <Output>
                <TextOutput file-format="csv"/>
            </Output>
            <Plots>
                <Plot time-step="0">
                    <Style style="lines" line-width="5.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="space.x"/>
                    </X-axis>
                    <Y-axis minimum="0" maximum="3">
                        <Symbol symbol-ref="a"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="i"/>
                    </Color-bar>
                    <Range>
                        <Data/>
                        <Time mode="current"/>
                    </Range>
                </Plot>
            </Plots>
            <Restriction>
                <Slice axis="y" value="size.y/2"/>
            </Restriction>
        </Logger>
        <Logger time-step="100">
            <Input>
                <Symbol symbol-ref="a"/>
            </Input>
            <Output>
                <TextOutput file-format="matrix"/>
            </Output>
            <Plots>
                <SurfacePlot time-step="500">
                    <Color-bar>
                        <Symbol symbol-ref="a"/>
                    </Color-bar>
                    <Terminal terminal="png"/>
                </SurfacePlot>
            </Plots>
            <Restriction>
                <Slice axis="y" value="size.y/2"/>
            </Restriction>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## ActivatorInhibitor_Domain

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-ActivatorInhibitor-2D-Domain</Title>
        <Details>Meinhardt-Gierer (activator-inhibitor) model solved in a nonregular domain with constant boundaries.</Details>
    </Description>
    <Global>
        <Field name="activator" value="rand_norm(0.5,0.1)" symbol="a">
            <Diffusion rate="0.02"/>
            <BoundaryValue boundary="domain" value="0.01"/>
        </Field>
        <Field name="inhibitor" value="0.1" symbol="i">
            <Diffusion rate="0.22"/>
            <BoundaryValue boundary="domain" value="0"/>
        </Field>
        <System name="Meinhardt" time-step="5" solver="Runge-Kutta [fixed, O(4)]">
            <Constant value="0.001" symbol="rho"/>
            <Constant value="0.001" symbol="rho_a"/>
            <Constant value="0.02" symbol="mu_i"/>
            <Constant value="0.04" symbol="mu_a"/>
            <Constant value="0.10" symbol="kappa"/>
            <DiffEqn symbol-ref="a">
                <Expression>(rho/i)*((a^2)/(1 + kappa*a^2)) - mu_a * a + rho_a</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="i">
                <Expression>rho*((a^2)/(1+kappa*a^2)) - mu_i *i</Expression>
            </DiffEqn>
        </System>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="100, 100, 0" symbol="size"/>
            <NodeLength value="1"/>
            <Domain boundary-type="constant">
                <Image path="assets/activator-inhibitor-domain.tif"/>
            </Domain>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="10000"/>
        <SaveInterval value="0"/>
        <RandomSeed value="2"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Gnuplotter decorate="false" time-step="200">
            <Terminal size="400 400 0" name="png"/>
            <Plot>
                <Field min="0" symbol-ref="a"/>
            </Plot>
        </Gnuplotter>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```

## ExcitableMedium_3D

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-ExcitableMedium-3D</Title>
        <Details>Simulates the Barkley model of an excitable medium, see: http://www.scholarpedia.org/article/Barkley_model
Derived from FitzHugh-Nagumo model and Hogdkin-Huxley model.

TIFF images can be viewed with external tools such as Fiji / ImageJ (http://fiji.sc/Fiji) or BioView3D (http://www.dimin.net/software/bioview3d/). The latter also reads the OME header for 3D, 4D and 5D images.
VTK filed can be viewed with external tools such as ParaView  (https://www.paraview.org/).</Details>
    </Description>
    <Global>
        <Field value="if( l.x>=s.x/2-5 and l.x&lt;=s.x/2+5 and l.z>=s.z/2-5 and l.z&lt;=s.z/2+5 and l.y&lt;=s.y/4 , 1, 0 )" symbol="u">
            <Diffusion rate="0.5"/>
        </Field>
        <Field value="if(l.x&lt;=s.x/2 and l.z&lt;=(3*s.z)/4, 1, 0)" symbol="v">
            <Diffusion rate="0.5"/>
        </Field>
        <System time-step="0.05" solver="Runge-Kutta [fixed, O(4)]">
            <DiffEqn symbol-ref="u">
                <Expression>(1/e)*u*(1-u)*(u-((v+b)/a))</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="v">
                <Expression>u-v</Expression>
            </DiffEqn>
            <Constant value="0.02" symbol="e"/>
            <Constant value="0.8" symbol="a"/>
            <Constant value="0.01" symbol="b"/>
        </System>
    </Global>
    <Space>
        <Lattice class="cubic">
            <Size value="50, 50, 50" symbol="s"/>
            <BoundaryConditions>
                <Condition type="noflux" boundary="x"/>
                <Condition type="noflux" boundary="y"/>
                <Condition type="noflux" boundary="z"/>
                <Condition type="noflux" boundary="-x"/>
                <Condition type="noflux" boundary="-y"/>
                <Condition type="noflux" boundary="-z"/>
            </BoundaryConditions>
            <NodeLength value="1.0"/>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="l" name="position in space"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="25"/>
        <SaveInterval value="0"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Gnuplotter time-step="5">
            <Terminal size="600 600 0" name="png"/>
            <Plot slice="25">
                <Field symbol-ref="u"/>
            </Plot>
        </Gnuplotter>
        <TiffPlotter compression="false" time-step="0.5" OME-header="true" format="32bit" timelapse="true">
            <Channel symbol-ref="u"/>
            <Channel symbol-ref="v"/>
        </TiffPlotter>
        <ModelGraph reduced="false" include-tags="#untagged" format="svg"/>
        <VtkPlotter mode="binary" time-step="0.5">
            <Channel symbol-ref="u"/>
            <Channel symbol-ref="v"/>
        </VtkPlotter>
    </Analysis>
</MorpheusModel>
```

## TuringPatterns

```xml
<MorpheusModel version="4">
    <Description>
        <Title>Example-TuringPatterns</Title>
        <Details>
Miyazawa, Okamoto and Kondo, Blending of animal colour patterns by hybridization, Nature Communications, 2010</Details>
    </Description>
    <Global>
        <Field value="4.1+rand_uni(0,1)" symbol="u">
            <Diffusion rate="1"/>
        </Field>
        <Field value="4.84+rand_uni(0,1)" symbol="v">
            <Diffusion rate="20"/>
        </Field>
        <System name="Miyazawa" time-step="0.25" solver="Runge-Kutta [fixed, O(4)]">
            <Function symbol="A">
                <Expression>0.07 + ((0.07 * l.y)/ s.y)</Expression>
            </Function>
            <Constant value="0.08" symbol="B"/>
            <Function symbol="C">
                <Expression>-0.1 + ((0.5 * l.x)/ s.x)</Expression>
            </Function>
            <Constant value="0.03" symbol="D"/>
            <Constant value="0.10" symbol="E"/>
            <Constant value="0.12" symbol="F"/>
            <Constant value="0.06" symbol="G"/>
            <Constant value="20.0" symbol="R"/>
            <Constant value="0.23" symbol="synU_max"/>
            <Constant value="0.50" symbol="synV_max"/>
            <Function symbol="s_u">
                <Expression>max( 0, min( synU_max, A()*u-B*v+C()))</Expression>
            </Function>
            <Function symbol="s_v">
                <Expression>max( 0, min( synV_max, E*u - F))</Expression>
            </Function>
            <DiffEqn symbol-ref="u">
                <Expression>R*(s_u() - D*u)</Expression>
            </DiffEqn>
            <DiffEqn symbol-ref="v">
                <Expression>R*(s_v() - G*v)</Expression>
            </DiffEqn>
        </System>
    </Global>
    <Space>
        <Lattice class="square">
            <Size value="512, 512, 0" symbol="s"/>
            <NodeLength value="1"/>
            <BoundaryConditions>
                <Condition boundary="x" type="noflux"/>
                <Condition boundary="y" type="noflux"/>
            </BoundaryConditions>
            <Neighborhood>
                <Order>1</Order>
            </Neighborhood>
        </Lattice>
        <SpaceSymbol symbol="l"/>
    </Space>
    <Time>
        <StartTime value="0"/>
        <StopTime value="30"/>
        <SaveInterval value="0"/>
        <RandomSeed value="1"/>
        <TimeSymbol symbol="time"/>
    </Time>
    <Analysis>
        <Gnuplotter decorate="false" time-step="2">
            <Terminal persist="true" name="png"/>
            <Plot>
                <Field symbol-ref="u">
                    <ColorMap>
                        <Color color="black" value="0.0"/>
                        <Color color="white" value="1.0"/>
                    </ColorMap>
                </Field>
            </Plot>
        </Gnuplotter>
        <Logger time-step="0.0">
            <Input>
                <Symbol symbol-ref="u"/>
            </Input>
            <Output>
                <TextOutput file-format="csv"/>
            </Output>
            <Restriction>
                <Slice axis="x" value="s.x/2"/>
            </Restriction>
            <Plots>
                <Plot title="slice at half of x extension" time-step="-1">
                    <Style style="lines" line-width="3.0"/>
                    <Terminal terminal="png"/>
                    <X-axis>
                        <Symbol symbol-ref="l.y"/>
                    </X-axis>
                    <Y-axis>
                        <Symbol symbol-ref="u"/>
                    </Y-axis>
                    <Color-bar>
                        <Symbol symbol-ref="v"/>
                    </Color-bar>
                </Plot>
            </Plots>
        </Logger>
        <Logger time-step="2">
            <Input>
                <Symbol symbol-ref="u"/>
            </Input>
            <Output>
                <TextOutput file-format="csv"/>
            </Output>
            <Plots>
                <SurfacePlot time-step="2">
                    <Color-bar>
                        <Symbol symbol-ref="u"/>
                    </Color-bar>
                    <Terminal terminal="png"/>
                </SurfacePlot>
            </Plots>
        </Logger>
        <ModelGraph include-tags="#untagged" format="svg" reduced="false"/>
    </Analysis>
</MorpheusModel>
```
